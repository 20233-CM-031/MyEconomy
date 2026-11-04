"""Owner-scoped financial data use cases and deterministic statement ingestion."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.domain.errors import (
    ConflictError,
    FinancialDataValidationError,
    IdempotencyConflictError,
    NotFoundError,
)
from myeconomy.domain.financial import (
    CsvRowError,
    ParsedTransaction,
    amount_to_minor_units,
    minor_units_to_decimal,
    parse_transaction_csv,
)
from myeconomy.domain.money import currency_exponent
from myeconomy.infrastructure.models import (
    FinancialAccount,
    FinancialTransaction,
    RecurringObligation,
    TransactionImportBatch,
    User,
    utc_now,
)

SUPPORTED_ACCOUNT_TYPES = {
    "BANK_DEPOSIT",
    "CREDIT_CARD",
    "UPI_WALLET",
    "CASH",
    "INVESTMENT",
    "OTHER",
}
SUPPORTED_FREQUENCIES = {"WEEKLY", "FORTNIGHTLY", "MONTHLY", "QUARTERLY", "YEARLY"}


@dataclass(frozen=True, slots=True)
class ImportOutcome:
    batch: TransactionImportBatch
    replayed: bool
    errors: tuple[dict[str, object], ...]


def _safe_filename(value: str) -> str:
    name = PurePath(value.replace("\\", "/")).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return (name or "statement.csv")[:160]


def _money_minor(value: Decimal, currency: str, *, signed: bool = False) -> int:
    if not value.is_finite():
        raise FinancialDataValidationError("Money values must be finite.")
    if signed and value == 0:
        return 0
    sign = -1 if value < 0 else 1
    return sign * amount_to_minor_units(abs(value), currency, allow_zero=not signed)


def create_financial_account(
    db: Session,
    *,
    owner: User,
    account_name: str,
    account_type: str,
    currency: str,
    institution_label: str | None = None,
    masked_reference: str | None = None,
    opening_balance: Decimal = Decimal("0"),
    opening_balance_as_of: date | None = None,
    source_type: str = "MANUAL",
    source_external_id: str | None = None,
) -> FinancialAccount:
    normalized_currency = currency.upper()
    try:
        exponent = currency_exponent(normalized_currency)
        opening_minor = _money_minor(opening_balance, normalized_currency, signed=True)
    except ValueError as exc:
        raise FinancialDataValidationError(str(exc)) from exc
    if account_type not in SUPPORTED_ACCOUNT_TYPES:
        raise FinancialDataValidationError("Unsupported financial account type.")
    if not account_name.strip() or len(account_name.strip()) > 100:
        raise FinancialDataValidationError("Account name must contain 1 to 100 characters.")
    if opening_balance.as_tuple().exponent < -exponent:
        raise FinancialDataValidationError("Opening balance exceeds the currency precision.")
    if source_type not in {"MANUAL", "CSV_IMPORT", "AUTHORIZED_PROVIDER", "SYNTHETIC_FIXTURE"}:
        raise FinancialDataValidationError("Unsupported account source type.")
    account = FinancialAccount(
        owner_user_id=owner.id,
        account_name=account_name.strip(),
        account_type=account_type,
        currency=normalized_currency,
        institution_label=(institution_label or "").strip()[:120] or None,
        masked_reference=(masked_reference or "").strip()[:64] or None,
        opening_balance_minor=opening_minor,
        opening_balance_as_of=opening_balance_as_of,
        status="ACTIVE",
        source_type=source_type,
        source_external_id=(source_external_id or "").strip()[:128] or None,
    )
    db.add(account)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=owner.id,
            action="financial.account.created",
            subject_type="financial_account",
            subject_id=str(account.id),
            details={
                "account_type": account_type,
                "currency": normalized_currency,
                "source_type": source_type,
            },
        )
        db.commit()
        db.refresh(account)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("An account with this source identity already exists.") from exc
    return account


def list_financial_accounts(db: Session, *, owner_user_id: UUID) -> list[FinancialAccount]:
    return list(
        db.scalars(
            select(FinancialAccount)
            .where(FinancialAccount.owner_user_id == owner_user_id)
            .order_by(FinancialAccount.created_at, FinancialAccount.id)
        ).all()
    )


def get_owned_account(db: Session, *, owner_user_id: UUID, account_id: UUID) -> FinancialAccount:
    account = db.scalar(
        select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.owner_user_id == owner_user_id,
        )
    )
    if account is None:
        raise NotFoundError("Financial account was not found.")
    return account


def _row_errors(errors: tuple[CsvRowError, ...]) -> list[dict[str, object]]:
    return [
        {"row_number": item.row_number, "code": item.code, "message": item.message}
        for item in errors
    ]


def _same_reference_fingerprint(existing: FinancialTransaction, row: ParsedTransaction) -> bool:
    return existing.fingerprint_sha256 == row.fingerprint_sha256


def _allowed_status_transition(current: str, incoming: str) -> bool:
    """Allow monotonic provider lifecycle updates; never reactivate terminal records."""
    if current == incoming:
        return True
    allowed = {
        "PENDING": {"POSTED", "REVERSED", "VOID"},
        "POSTED": {"REVERSED", "VOID"},
        "REVERSED": set(),
        "VOID": set(),
    }
    return incoming in allowed.get(current, set())


def import_transactions_csv(
    db: Session,
    *,
    owner: User,
    account_id: UUID,
    idempotency_key: str,
    filename: str,
    content: bytes,
) -> ImportOutcome:
    """Atomically import one statement, with batch and provider-reference idempotency."""
    get_owned_account(db, owner_user_id=owner.id, account_id=account_id)
    key = idempotency_key.strip()
    if not key or len(key) > 128 or not all(ch.isprintable() for ch in key):
        raise FinancialDataValidationError(
            "Idempotency-Key must contain 1 to 128 printable characters."
        )
    source_hash = hashlib.sha256(content).hexdigest()
    existing_batch = db.scalar(
        select(TransactionImportBatch).where(
            TransactionImportBatch.owner_user_id == owner.id,
            TransactionImportBatch.idempotency_key == key,
        )
    )
    if existing_batch is not None:
        if existing_batch.source_sha256 != source_hash or existing_batch.account_id != account_id:
            raise IdempotencyConflictError()
        return ImportOutcome(existing_batch, True, tuple(existing_batch.validation_errors or []))

    account = get_owned_account(db, owner_user_id=owner.id, account_id=account_id)
    if account.status != "ACTIVE":
        raise FinancialDataValidationError(
            "Transactions cannot be imported into an inactive or closed account."
        )
    batch = TransactionImportBatch(
        owner_user_id=owner.id,
        account_id=account.id,
        idempotency_key=key,
        source_sha256=source_hash,
        source_filename=_safe_filename(filename),
        source_type="CSV_IMPORT",
        status="REJECTED",
        row_count=0,
        inserted_count=0,
        updated_count=0,
        duplicate_count=0,
        potential_duplicate_count=0,
        validation_errors=[],
        created_at=utc_now(),
    )
    db.add(batch)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "A concurrent import used this idempotency key. Retry the same request."
        ) from exc

    try:
        parsed = parse_transaction_csv(content, account_currency=account.currency)
    except ValueError as exc:
        batch.validation_errors = [{"row_number": 0, "code": "invalid_csv", "message": str(exc)}]
        batch.row_count = 0
        batch.status = "REJECTED"
        batch.completed_at = utc_now()
        record_audit_event(
            db,
            actor_user_id=owner.id,
            action="financial.csv_import.rejected",
            subject_type="transaction_import_batch",
            subject_id=str(batch.id),
            details={"account_id": str(account.id), "source_sha256": source_hash, "error_count": 1},
        )
        db.commit()
        db.refresh(batch)
        return ImportOutcome(batch, False, tuple(batch.validation_errors))

    batch.row_count = len(parsed.rows) + len(parsed.errors)
    errors = _row_errors(parsed.errors)
    if errors:
        batch.validation_errors = errors
        batch.status = "REJECTED"
        batch.completed_at = utc_now()
        record_audit_event(
            db,
            actor_user_id=owner.id,
            action="financial.csv_import.rejected",
            subject_type="transaction_import_batch",
            subject_id=str(batch.id),
            details={
                "account_id": str(account.id),
                "source_sha256": source_hash,
                "error_count": len(errors),
            },
        )
        db.commit()
        db.refresh(batch)
        return ImportOutcome(batch, False, tuple(errors))

    rows = list(parsed.rows)
    references = [r.external_reference for r in rows if r.external_reference]
    existing_by_ref: dict[str, FinancialTransaction] = {}
    for start in range(0, len(references), 500):
        chunk = references[start : start + 500]
        found = db.scalars(
            select(FinancialTransaction).where(
                FinancialTransaction.owner_user_id == owner.id,
                FinancialTransaction.account_id == account.id,
                FinancialTransaction.external_reference.in_(chunk),
            )
        ).all()
        existing_by_ref.update(
            {item.external_reference: item for item in found if item.external_reference}
        )

    # External references are authoritative provider identifiers. A changed economic
    # payload for the same identifier rejects the entire import, not just that row.
    in_batch_refs: dict[str, ParsedTransaction] = {}
    for row in rows:
        if not row.external_reference:
            continue
        prior_in_file = in_batch_refs.get(row.external_reference)
        if prior_in_file:
            if (
                prior_in_file.fingerprint_sha256 != row.fingerprint_sha256
                or prior_in_file.status != row.status
            ):
                errors.append(
                    {
                        "row_number": row.row_number,
                        "code": "external_reference_conflict",
                        "message": (
                            "The same external reference appears more than once with conflicting "
                            "financial content or lifecycle state."
                        ),
                    }
                )
            continue
        in_batch_refs[row.external_reference] = row
        existing = existing_by_ref.get(row.external_reference)
        if existing and not _same_reference_fingerprint(existing, row):
            errors.append(
                {
                    "row_number": row.row_number,
                    "code": "external_reference_conflict",
                    "message": (
                        "An imported reference already exists with different transaction content."
                    ),
                }
            )
        elif existing and not _allowed_status_transition(existing.status, row.status):
            errors.append(
                {
                    "row_number": row.row_number,
                    "code": "invalid_status_transition",
                    "message": (
                        f"Transaction status cannot move from {existing.status} to {row.status}."
                    ),
                }
            )

    if errors:
        batch.validation_errors = errors
        batch.status = "REJECTED"
        batch.completed_at = utc_now()
        record_audit_event(
            db,
            actor_user_id=owner.id,
            action="financial.csv_import.rejected",
            subject_type="transaction_import_batch",
            subject_id=str(batch.id),
            details={
                "account_id": str(account.id),
                "source_sha256": source_hash,
                "error_count": len(errors),
            },
        )
        db.commit()
        db.refresh(batch)
        return ImportOutcome(batch, False, tuple(errors))

    fingerprints = list({row.fingerprint_sha256 for row in rows})
    prior_by_fingerprint: dict[str, FinancialTransaction] = {}
    for start in range(0, len(fingerprints), 500):
        chunk = fingerprints[start : start + 500]
        found = db.scalars(
            select(FinancialTransaction).where(
                FinancialTransaction.owner_user_id == owner.id,
                FinancialTransaction.account_id == account.id,
                FinancialTransaction.fingerprint_sha256.in_(chunk),
                FinancialTransaction.status == "POSTED",
            )
        ).all()
        for item in found:
            prior_by_fingerprint.setdefault(item.fingerprint_sha256, item)

    first_in_batch: dict[str, UUID] = {}
    seen_external_references: set[str] = set()
    duplicate_count = 0
    updated_count = 0
    potential_count = 0
    inserted_count = 0
    for row in rows:
        if row.external_reference:
            existing = existing_by_ref.get(row.external_reference)
            if existing:
                prior_status = existing.status
                metadata_enriched = existing.posted_at is None and row.posted_at is not None
                if prior_status != row.status or metadata_enriched:
                    existing.status = row.status
                    if row.posted_at is not None and existing.posted_at is None:
                        existing.posted_at = row.posted_at
                    updated_count += 1
                    record_audit_event(
                        db,
                        actor_user_id=owner.id,
                        action="financial.transaction.provider_state_reconciled",
                        subject_type="financial_transaction",
                        subject_id=str(existing.id),
                        details={
                            "from_status": prior_status,
                            "to_status": row.status,
                            "metadata_enriched": metadata_enriched,
                            "source_import_batch_id": str(batch.id),
                            "source_row_number": row.row_number,
                        },
                    )
                else:
                    duplicate_count += 1
                continue
            duplicate_in_file = row.external_reference in seen_external_references
            if duplicate_in_file:
                duplicate_count += 1
                continue
        transaction_id = uuid4()
        potential_match = prior_by_fingerprint.get(row.fingerprint_sha256)
        if potential_match is None and row.fingerprint_sha256 in first_in_batch:
            potential_match_id = first_in_batch[row.fingerprint_sha256]
        else:
            potential_match_id = potential_match.id if potential_match else None
        transaction = FinancialTransaction(
            id=transaction_id,
            owner_user_id=owner.id,
            account_id=account.id,
            import_batch_id=batch.id,
            occurred_on=row.occurred_on,
            posted_at=row.posted_at,
            amount_minor=row.amount_minor,
            currency=row.currency,
            direction=row.direction,
            cashflow_treatment=row.cashflow_treatment,
            category=row.category,
            description=row.description,
            counterparty_label=row.counterparty_label,
            external_reference=row.external_reference,
            status=row.status,
            essential=row.essential,
            fingerprint_sha256=row.fingerprint_sha256,
            potential_duplicate_of_id=potential_match_id,
            source_row_number=row.row_number,
        )
        db.add(transaction)
        if row.external_reference:
            seen_external_references.add(row.external_reference)
        if row.fingerprint_sha256 not in first_in_batch:
            first_in_batch[row.fingerprint_sha256] = transaction_id
        if potential_match_id:
            potential_count += 1
        inserted_count += 1

    batch.inserted_count = inserted_count
    batch.updated_count = updated_count
    batch.duplicate_count = duplicate_count
    batch.potential_duplicate_count = potential_count
    batch.status = "PARTIAL" if duplicate_count and inserted_count else "COMPLETED"
    batch.completed_at = utc_now()
    record_audit_event(
        db,
        actor_user_id=owner.id,
        action="financial.csv_import.completed",
        subject_type="transaction_import_batch",
        subject_id=str(batch.id),
        details={
            "account_id": str(account.id),
            "source_sha256": source_hash,
            "row_count": batch.row_count,
            "inserted_count": inserted_count,
            "updated_count": updated_count,
            "duplicate_count": duplicate_count,
            "potential_duplicate_count": potential_count,
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "The import conflicted with a concurrent update. Retry with the same idempotency key."
        ) from exc
    db.refresh(batch)
    return ImportOutcome(batch, False, ())


def get_import_batch(db: Session, *, owner_user_id: UUID, batch_id: UUID) -> TransactionImportBatch:
    batch = db.scalar(
        select(TransactionImportBatch).where(
            TransactionImportBatch.id == batch_id,
            TransactionImportBatch.owner_user_id == owner_user_id,
        )
    )
    if batch is None:
        raise NotFoundError("Transaction import batch was not found.")
    return batch


def list_transactions(
    db: Session,
    *,
    owner_user_id: UUID,
    account_id: UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[FinancialTransaction]:
    get_owned_account(db, owner_user_id=owner_user_id, account_id=account_id)
    return list(
        db.scalars(
            select(FinancialTransaction)
            .where(
                FinancialTransaction.owner_user_id == owner_user_id,
                FinancialTransaction.account_id == account_id,
            )
            .order_by(FinancialTransaction.occurred_on.desc(), FinancialTransaction.id)
            .limit(limit)
            .offset(offset)
        ).all()
    )


def analyze_persisted_cashflow(
    db: Session,
    *,
    owner_user_id: UUID,
    currency: str,
    period_start: date,
    period_end: date,
) -> dict[str, object]:
    if period_end < period_start:
        raise FinancialDataValidationError("period_end must be on or after period_start.")
    normalized_currency = currency.upper()
    try:
        currency_exponent(normalized_currency)
    except ValueError as exc:
        raise FinancialDataValidationError(str(exc)) from exc
    rows = db.execute(
        select(
            FinancialTransaction.cashflow_treatment,
            FinancialTransaction.direction,
            FinancialTransaction.amount_minor,
            FinancialTransaction.essential,
        ).where(
            FinancialTransaction.owner_user_id == owner_user_id,
            FinancialTransaction.currency == normalized_currency,
            FinancialTransaction.occurred_on >= period_start,
            FinancialTransaction.occurred_on <= period_end,
            FinancialTransaction.status == "POSTED",
        )
    ).all()
    income = 0
    expenses = 0
    refunds = 0
    essential_expenses = 0
    for treatment, direction, amount, essential in rows:
        if treatment == "INCOME" and direction == "CREDIT":
            income += amount
        elif treatment == "EXPENSE" and direction == "DEBIT":
            expenses += amount
            if essential:
                essential_expenses += amount
        elif treatment == "REFUND" and direction == "CREDIT":
            refunds += amount
    net_expenses = expenses - refunds
    net_cashflow = income - expenses + refunds
    return {
        "currency": normalized_currency,
        "period_start": period_start,
        "period_end": period_end,
        "posted_transaction_count": len(rows),
        "income_total": minor_units_to_decimal(income, normalized_currency),
        "gross_expenses": minor_units_to_decimal(expenses, normalized_currency),
        "refunds": minor_units_to_decimal(refunds, normalized_currency),
        "net_expenses_after_refunds": minor_units_to_decimal(net_expenses, normalized_currency),
        "essential_expenses_before_refunds": minor_units_to_decimal(
            essential_expenses, normalized_currency
        ),
        "discretionary_expenses_before_refunds": minor_units_to_decimal(
            expenses - essential_expenses, normalized_currency
        ),
        "net_cashflow": minor_units_to_decimal(net_cashflow, normalized_currency),
        "net_cashflow_to_income_percent": (
            (Decimal(net_cashflow) / Decimal(income) * Decimal("100")).quantize(Decimal("0.01"))
            if income
            else None
        ),
        "pending_transactions_excluded": True,
        "transfer_and_ignore_treatments_excluded": True,
        "savings_warning": (
            "Net cashflow is based only on posted, imported records in this currency and period. "
            "It is not a verified bank balance or complete savings measure."
        ),
    }


def create_recurring_obligation(
    db: Session,
    *,
    owner: User,
    payee_label: str,
    category: str,
    amount: Decimal,
    currency: str,
    frequency: str,
    first_due_date: date,
    next_due_date: date,
    due_day: int | None = None,
    account_id: UUID | None = None,
    autopay_enabled: bool = False,
    essential: bool = False,
    source_type: str = "MANUAL",
    source_external_id: str | None = None,
) -> RecurringObligation:
    normalized_currency = currency.upper()
    try:
        amount_minor = amount_to_minor_units(amount, normalized_currency)
    except ValueError as exc:
        raise FinancialDataValidationError(str(exc)) from exc
    if frequency not in SUPPORTED_FREQUENCIES:
        raise FinancialDataValidationError("Unsupported recurring-obligation frequency.")
    if due_day is not None and not 1 <= due_day <= 31:
        raise FinancialDataValidationError("Due day must be between 1 and 31.")
    if next_due_date < first_due_date:
        raise FinancialDataValidationError("Next due date cannot precede the first due date.")
    if not payee_label.strip() or len(payee_label.strip()) > 128:
        raise FinancialDataValidationError("Payee label must contain 1 to 128 characters.")
    if account_id:
        account = get_owned_account(db, owner_user_id=owner.id, account_id=account_id)
        if account.currency != normalized_currency:
            raise FinancialDataValidationError("Obligation currency must match its linked account.")
    obligation = RecurringObligation(
        owner_user_id=owner.id,
        account_id=account_id,
        payee_label=payee_label.strip(),
        category=category.strip()[:64] or "uncategorized",
        amount_minor=amount_minor,
        currency=normalized_currency,
        frequency=frequency,
        due_day=due_day,
        first_due_date=first_due_date,
        next_due_date=next_due_date,
        autopay_enabled=autopay_enabled,
        essential=essential,
        status="ACTIVE",
        source_type=source_type,
        source_external_id=(source_external_id or "").strip()[:128] or None,
    )
    db.add(obligation)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=owner.id,
        action="financial.obligation.created",
        subject_type="recurring_obligation",
        subject_id=str(obligation.id),
        details={"currency": normalized_currency, "frequency": frequency, "essential": essential},
    )
    db.commit()
    db.refresh(obligation)
    return obligation


def list_recurring_obligations(db: Session, *, owner_user_id: UUID) -> list[RecurringObligation]:
    return list(
        db.scalars(
            select(RecurringObligation)
            .where(RecurringObligation.owner_user_id == owner_user_id)
            .order_by(RecurringObligation.next_due_date, RecurringObligation.id)
        ).all()
    )
