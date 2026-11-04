"""Owner-scoped financial account, import, obligation and cashflow APIs."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from myeconomy.api.dependencies import AuthContext, require_verified_authentication
from myeconomy.api.financial_schemas import (
    CashflowResponse,
    FinancialAccountCreateRequest,
    FinancialAccountResponse,
    ImportResponse,
    RecurringObligationCreateRequest,
    RecurringObligationResponse,
    TransactionResponse,
)
from myeconomy.application.financial import (
    analyze_persisted_cashflow,
    create_financial_account,
    create_recurring_obligation,
    get_import_batch,
    import_transactions_csv,
    list_financial_accounts,
    list_recurring_obligations,
    list_transactions,
)
from myeconomy.domain.financial import MAX_CSV_BYTES, minor_units_to_decimal
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.models import (
    FinancialAccount,
    FinancialTransaction,
    RecurringObligation,
)

router = APIRouter(prefix="/api/v1/financial", tags=["financial-data"])


def _utc(value: datetime) -> datetime:
    """Normalize DB-returned timestamps; SQLite may drop timezone metadata."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _account_response(account: FinancialAccount) -> FinancialAccountResponse:
    return FinancialAccountResponse(
        id=account.id,
        account_name=account.account_name,
        account_type=account.account_type,
        currency=account.currency,
        institution_label=account.institution_label,
        masked_reference=account.masked_reference,
        opening_balance=minor_units_to_decimal(account.opening_balance_minor, account.currency),
        opening_balance_as_of=account.opening_balance_as_of,
        status=account.status,
        source_type=account.source_type,
        created_at=_utc(account.created_at),
    )


def _transaction_response(item: FinancialTransaction) -> TransactionResponse:
    return TransactionResponse(
        id=item.id,
        account_id=item.account_id,
        occurred_on=item.occurred_on,
        posted_at=_utc(item.posted_at) if item.posted_at is not None else None,
        amount=minor_units_to_decimal(item.amount_minor, item.currency),
        currency=item.currency,
        direction=item.direction,
        cashflow_treatment=item.cashflow_treatment,
        category=item.category,
        description=item.description,
        counterparty_label=item.counterparty_label,
        external_reference=item.external_reference,
        status=item.status,
        essential=item.essential,
        potential_duplicate_of_id=item.potential_duplicate_of_id,
    )


def _obligation_response(item: RecurringObligation) -> RecurringObligationResponse:
    return RecurringObligationResponse(
        id=item.id,
        account_id=item.account_id,
        payee_label=item.payee_label,
        category=item.category,
        amount=minor_units_to_decimal(item.amount_minor, item.currency),
        currency=item.currency,
        frequency=item.frequency,
        due_day=item.due_day,
        first_due_date=item.first_due_date,
        next_due_date=item.next_due_date,
        autopay_enabled=item.autopay_enabled,
        essential=item.essential,
        status=item.status,
    )


@router.post(
    "/accounts", response_model=FinancialAccountResponse, status_code=status.HTTP_201_CREATED
)
def create_account_endpoint(
    payload: FinancialAccountCreateRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> FinancialAccountResponse:
    account = create_financial_account(
        db,
        owner=auth.user,
        account_name=payload.account_name,
        account_type=payload.account_type,
        currency=payload.currency,
        institution_label=payload.institution_label,
        masked_reference=payload.masked_reference,
        opening_balance=payload.opening_balance,
        opening_balance_as_of=payload.opening_balance_as_of,
    )
    return _account_response(account)


@router.get("/accounts", response_model=list[FinancialAccountResponse])
def list_accounts_endpoint(
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[FinancialAccountResponse]:
    return [
        _account_response(item) for item in list_financial_accounts(db, owner_user_id=auth.user.id)
    ]


@router.post("/accounts/{account_id}/imports/csv", response_model=ImportResponse)
async def import_csv_endpoint(
    account_id: UUID,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    filename: str = Header(default="statement.csv", alias="X-Filename", max_length=256),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> ImportResponse | JSONResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {
        "text/csv",
        "application/csv",
        "application/octet-stream",
        "text/plain",
    }:
        return JSONResponse(
            status_code=415,
            content={
                "error": {
                    "code": "unsupported_media_type",
                    "message": "Upload a CSV file using text/csv content type.",
                }
            },
        )
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_CSV_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "payload_too_large",
                    "message": "CSV file exceeds the 2 MiB limit.",
                }
            },
        )
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_CSV_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "payload_too_large",
                        "message": "CSV file exceeds the 2 MiB limit.",
                    }
                },
            )
        body.extend(chunk)
    content = bytes(body)
    outcome = import_transactions_csv(
        db,
        owner=auth.user,
        account_id=account_id,
        idempotency_key=idempotency_key,
        filename=filename,
        content=content,
    )
    batch = outcome.batch
    body = ImportResponse(
        batch_id=batch.id,
        status=batch.status,
        source_sha256=batch.source_sha256,
        row_count=batch.row_count,
        inserted_count=batch.inserted_count,
        updated_count=batch.updated_count,
        duplicate_count=batch.duplicate_count,
        potential_duplicate_count=batch.potential_duplicate_count,
        replayed=outcome.replayed,
        validation_errors=outcome.errors,
    )
    if batch.status == "REJECTED":
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
    return body


@router.get("/imports/{batch_id}", response_model=ImportResponse)
def get_import_endpoint(
    batch_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> ImportResponse:
    batch = get_import_batch(db, owner_user_id=auth.user.id, batch_id=batch_id)
    return ImportResponse(
        batch_id=batch.id,
        status=batch.status,
        source_sha256=batch.source_sha256,
        row_count=batch.row_count,
        inserted_count=batch.inserted_count,
        updated_count=batch.updated_count,
        duplicate_count=batch.duplicate_count,
        potential_duplicate_count=batch.potential_duplicate_count,
        replayed=False,
        validation_errors=batch.validation_errors or [],
    )


@router.get("/accounts/{account_id}/transactions", response_model=list[TransactionResponse])
def list_transactions_endpoint(
    account_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=100_000),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[TransactionResponse]:
    rows = list_transactions(
        db, owner_user_id=auth.user.id, account_id=account_id, limit=limit, offset=offset
    )
    return [_transaction_response(item) for item in rows]


@router.get("/cashflow", response_model=CashflowResponse)
def persisted_cashflow_endpoint(
    period_start: date,
    period_end: date,
    currency: str = Query(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> CashflowResponse:
    result = analyze_persisted_cashflow(
        db,
        owner_user_id=auth.user.id,
        currency=currency,
        period_start=period_start,
        period_end=period_end,
    )
    return CashflowResponse(**result)


@router.post(
    "/obligations", response_model=RecurringObligationResponse, status_code=status.HTTP_201_CREATED
)
def create_obligation_endpoint(
    payload: RecurringObligationCreateRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> RecurringObligationResponse:
    item = create_recurring_obligation(
        db,
        owner=auth.user,
        payee_label=payload.payee_label,
        category=payload.category,
        amount=payload.amount,
        currency=payload.currency,
        frequency=payload.frequency,
        first_due_date=payload.first_due_date,
        next_due_date=payload.next_due_date,
        due_day=payload.due_day,
        account_id=payload.account_id,
        autopay_enabled=payload.autopay_enabled,
        essential=payload.essential,
    )
    return _obligation_response(item)


@router.get("/obligations", response_model=list[RecurringObligationResponse])
def list_obligations_endpoint(
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[RecurringObligationResponse]:
    return [
        _obligation_response(item)
        for item in list_recurring_obligations(db, owner_user_id=auth.user.id)
    ]
