"""Financial-domain value objects and strict CSV statement parsing.

This module has no FastAPI, SQLAlchemy or provider dependencies. It normalizes
external statement rows into a canonical, auditable transaction representation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Literal

from myeconomy.domain.money import MoneyInputError, currency_exponent, quantize_amount

Direction = Literal["CREDIT", "DEBIT"]
CashflowTreatment = Literal["INCOME", "EXPENSE", "REFUND", "TRANSFER", "IGNORE"]
TransactionStatus = Literal["POSTED", "PENDING", "REVERSED", "VOID"]

MAX_CSV_BYTES = 2 * 1024 * 1024
MAX_MINOR_UNITS = 9_000_000_000_000_000_000  # conservative signed-BIGINT ceiling
MAX_CSV_ROWS = 10_000
MAX_CSV_COLUMNS = 32
MAX_DESCRIPTION_LENGTH = 256
MAX_COUNTERPARTY_LENGTH = 128
MAX_CATEGORY_LENGTH = 64

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "occurred_on": ("date", "transaction_date", "occurred_on", "transactiondate"),
    "amount": ("amount", "amount_inr", "transaction_amount", "value"),
    "currency": ("currency", "currency_code", "ccy"),
    "direction": ("direction", "dr_cr", "debit_credit", "transaction_direction"),
    "treatment": ("cashflow_treatment", "treatment", "cashflow_type"),
    "category": ("category", "expense_category", "transaction_category"),
    "description": ("description", "narration", "details", "transaction_description"),
    "counterparty": ("counterparty_label", "counterparty", "merchant", "payee", "payer"),
    "external_reference": (
        "external_transaction_id",
        "source_transaction_id",
        "reference",
        "transaction_id",
        "txn_id",
    ),
    "status": ("status", "transaction_status"),
    "posted_at": ("posted_at", "value_date_time", "booking_timestamp"),
    "essential": ("essential", "is_essential"),
}


@dataclass(frozen=True, slots=True)
class ParsedTransaction:
    row_number: int
    occurred_on: date
    amount_minor: int
    currency: str
    direction: Direction
    cashflow_treatment: CashflowTreatment
    category: str
    description: str
    counterparty_label: str | None
    external_reference: str | None
    status: TransactionStatus
    posted_at: datetime | None
    essential: bool
    fingerprint_sha256: str


@dataclass(frozen=True, slots=True)
class CsvRowError:
    row_number: int
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CsvParseResult:
    rows: tuple[ParsedTransaction, ...]
    errors: tuple[CsvRowError, ...]
    skipped_blank_rows: int

    @property
    def is_valid(self) -> bool:
        return not self.errors


def amount_to_minor_units(amount: Decimal, currency: str, *, allow_zero: bool = False) -> int:
    """Convert a Decimal amount to integer minor units without rounding loss."""
    exponent = currency_exponent(currency)
    if not amount.is_finite():
        raise MoneyInputError("Amount must be finite")
    if allow_zero and amount == 0:
        return 0
    normalized = quantize_amount(amount, currency)
    minor = int(normalized.scaleb(exponent))
    if minor > MAX_MINOR_UNITS:
        raise MoneyInputError("Amount exceeds the supported integer minor-unit range")
    return minor


def minor_units_to_decimal(amount_minor: int, currency: str) -> Decimal:
    """Render integer minor units as a Decimal with the currency's precision."""
    exponent = currency_exponent(currency)
    return Decimal(amount_minor).scaleb(-exponent)


def normalize_header(value: str) -> str:
    normalized = value.strip().lstrip("\ufeff").casefold()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def _header_map(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        raise ValueError("CSV file has no header row")
    if len(fieldnames) > MAX_CSV_COLUMNS:
        raise ValueError(f"CSV contains more than {MAX_CSV_COLUMNS} columns")
    normalized_headers = [normalize_header(item or "") for item in fieldnames]
    if any(not item for item in normalized_headers):
        raise ValueError("CSV contains an empty column name")
    if len(normalized_headers) != len(set(normalized_headers)):
        raise ValueError("CSV contains duplicate column names after normalization")
    result: dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in normalized_headers:
                result[canonical] = alias
                break
    missing = [name for name in ("occurred_on", "amount", "direction") if name not in result]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    return result


def _required_text(row: dict[str, str | None], header: str, *, label: str) -> str:
    value = (row.get(header) or "").strip()
    if not value:
        raise ValueError(f"{label} is required")
    return value


def _clean_text(value: str | None, *, label: str, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.replace("\x00", "").split())
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"{label} exceeds {max_length} characters")
    return cleaned


def _parse_status(value: str | None) -> TransactionStatus:
    normalized = (value or "POSTED").strip().upper()
    normalized = normalized.removesuffix("_FIXTURE")
    if normalized in {"POSTED", "SETTLED", "BOOKED", "CLEARED"}:
        return "POSTED"
    if normalized in {"PENDING", "PROCESSING"}:
        return "PENDING"
    if normalized in {"REVERSED", "REVERSAL"}:
        return "REVERSED"
    if normalized in {"VOID", "CANCELLED", "CANCELED"}:
        return "VOID"
    raise ValueError(f"Unsupported transaction status: {normalized}")


def _parse_direction(value: str) -> Direction:
    normalized = value.strip().upper()
    if normalized in {"CREDIT", "CR", "C"}:
        return "CREDIT"
    if normalized in {"DEBIT", "DR", "D"}:
        return "DEBIT"
    raise ValueError("Direction must be CREDIT or DEBIT")


def _parse_treatment(value: str | None, *, direction: Direction) -> CashflowTreatment:
    normalized = (value or "").strip().upper()
    if not normalized:
        # Direction alone cannot distinguish salary from an internal transfer,
        # loan drawdown or card settlement. Exclude from cashflow until classified.
        normalized = "IGNORE"
    normalized = normalized.removesuffix("_FIXTURE")
    allowed = {"INCOME", "EXPENSE", "REFUND", "TRANSFER", "IGNORE"}
    if normalized not in allowed:
        raise ValueError(f"Unsupported cashflow treatment: {normalized}")
    if normalized == "INCOME" and direction != "CREDIT":
        raise ValueError("INCOME transactions must have CREDIT direction")
    if normalized == "EXPENSE" and direction != "DEBIT":
        raise ValueError("EXPENSE transactions must have DEBIT direction")
    if normalized == "REFUND" and direction != "CREDIT":
        raise ValueError("REFUND transactions must have CREDIT direction")
    return normalized  # type: ignore[return-value]


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None or not value.strip():
        return default
    normalized = value.strip().casefold()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError("Essential flag must be true or false")


def _parse_posted_at(value: str | None) -> datetime | None:
    if value is None or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("posted_at must include a timezone offset")
    return parsed.astimezone(UTC)


def _fingerprint(
    *,
    occurred_on: date,
    amount_minor: int,
    currency: str,
    direction: Direction,
    category: str,
    description: str,
    counterparty: str | None,
    treatment: CashflowTreatment,
) -> str:
    canonical = "|".join(
        (
            occurred_on.isoformat(),
            str(amount_minor),
            currency,
            direction,
            treatment,
            category.casefold(),
            description.casefold(),
            (counterparty or "").casefold(),
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_transaction_csv(content: bytes, *, account_currency: str) -> CsvParseResult:
    """Parse a bounded CSV statement into normalized, currency-safe transactions.

    The parser never silently rounds money, coerces dates, changes currencies or
    infers that a transfer is income/expense. Any invalid row rejects the whole
    import batch at the application layer.
    """
    if not content:
        raise ValueError("CSV file is empty")
    if len(content) > MAX_CSV_BYTES:
        raise ValueError(f"CSV file exceeds the {MAX_CSV_BYTES}-byte limit")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc
    try:
        reader = csv.DictReader(io.StringIO(decoded, newline=""), strict=True)
        header_map = _header_map(reader.fieldnames)
    except (csv.Error, ValueError) as exc:
        raise ValueError(str(exc)) from exc

    normalized_currency = account_currency.upper()
    currency_exponent(normalized_currency)
    if header_map["amount"] == "amount_inr" and normalized_currency != "INR":
        raise ValueError("The amount_inr column can only be imported into an INR account.")
    parsed_rows: list[ParsedTransaction] = []
    errors: list[CsvRowError] = []
    skipped_blank_rows = 0

    try:
        for row_number, row in enumerate(reader, start=2):
            if row is None or all(not (value or "").strip() for value in row.values()):
                skipped_blank_rows += 1
                continue
            if None in row:
                errors.append(
                    CsvRowError(
                        row_number, "unexpected_columns", "Row has more values than the header"
                    )
                )
                continue
            if len(parsed_rows) + len(errors) >= MAX_CSV_ROWS:
                raise ValueError(f"CSV contains more than {MAX_CSV_ROWS} data rows")
            try:
                occurred_on = date.fromisoformat(
                    _required_text(row, header_map["occurred_on"], label="Date")
                )
                raw_amount = _required_text(row, header_map["amount"], label="Amount")
                try:
                    amount = Decimal(raw_amount)
                except InvalidOperation as exc:
                    raise ValueError(
                        "Amount must be a decimal number using a period as the decimal separator"
                    ) from exc
                amount_minor = amount_to_minor_units(amount, normalized_currency)
                currency_header = header_map.get("currency")
                row_currency = (
                    (row.get(currency_header) or normalized_currency).strip().upper()
                    if currency_header
                    else normalized_currency
                )
                if row_currency != normalized_currency:
                    raise ValueError(
                        f"Currency {row_currency} does not match account currency "
                        f"{normalized_currency}; FX conversion is not performed"
                    )
                direction = _parse_direction(
                    _required_text(row, header_map["direction"], label="Direction")
                )
                category_header = header_map.get("category")
                category = (
                    (row.get(category_header) or "uncategorized").strip()
                    if category_header
                    else "uncategorized"
                )
                category = (
                    _clean_text(category, label="Category", max_length=MAX_CATEGORY_LENGTH)
                    or "uncategorized"
                )
                description_header = header_map.get("description")
                description_raw = row.get(description_header) if description_header else None
                counterparty_header = header_map.get("counterparty")
                counterparty = _clean_text(
                    row.get(counterparty_header) if counterparty_header else None,
                    label="Counterparty",
                    max_length=MAX_COUNTERPARTY_LENGTH,
                )
                description = (
                    _clean_text(
                        description_raw or counterparty or category,
                        label="Description",
                        max_length=MAX_DESCRIPTION_LENGTH,
                    )
                    or category
                )
                treatment_header = header_map.get("treatment")
                treatment = _parse_treatment(
                    row.get(treatment_header) if treatment_header else None,
                    direction=direction,
                )
                status_header = header_map.get("status")
                status = _parse_status(row.get(status_header) if status_header else None)
                posted_header = header_map.get("posted_at")
                posted_at = _parse_posted_at(row.get(posted_header) if posted_header else None)
                external_header = header_map.get("external_reference")
                external_reference = _clean_text(
                    row.get(external_header) if external_header else None,
                    label="External reference",
                    max_length=128,
                )
                essential_header = header_map.get("essential")
                essential = _parse_bool(row.get(essential_header) if essential_header else None)
                fingerprint = _fingerprint(
                    occurred_on=occurred_on,
                    amount_minor=amount_minor,
                    currency=normalized_currency,
                    direction=direction,
                    category=category,
                    description=description,
                    counterparty=counterparty,
                    treatment=treatment,
                )
                parsed_rows.append(
                    ParsedTransaction(
                        row_number=row_number,
                        occurred_on=occurred_on,
                        amount_minor=amount_minor,
                        currency=normalized_currency,
                        direction=direction,
                        cashflow_treatment=treatment,
                        category=category,
                        description=description,
                        counterparty_label=counterparty,
                        external_reference=external_reference,
                        status=status,
                        posted_at=posted_at,
                        essential=essential,
                        fingerprint_sha256=fingerprint,
                    )
                )
            except (ValueError, MoneyInputError) as exc:
                errors.append(CsvRowError(row_number, "invalid_row", str(exc)))
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {exc}") from exc

    if not parsed_rows and not errors:
        raise ValueError("CSV contains no transaction rows")
    return CsvParseResult(tuple(parsed_rows), tuple(errors), skipped_blank_rows)
