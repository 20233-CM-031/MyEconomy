"""Typed request/response contracts for private financial records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FinancialAccountCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_name: str = Field(min_length=1, max_length=100)
    account_type: Literal[
        "BANK_DEPOSIT", "CREDIT_CARD", "UPI_WALLET", "CASH", "INVESTMENT", "OTHER"
    ]
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    institution_label: str | None = Field(default=None, max_length=120)
    masked_reference: str | None = Field(default=None, max_length=64)
    opening_balance: Decimal = Decimal("0")
    opening_balance_as_of: date | None = None


class FinancialAccountResponse(BaseModel):
    id: UUID
    account_name: str
    account_type: str
    currency: str
    institution_label: str | None
    masked_reference: str | None
    opening_balance: Decimal
    opening_balance_as_of: date | None
    status: str
    source_type: str
    created_at: datetime


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    occurred_on: date
    posted_at: datetime | None
    amount: Decimal
    currency: str
    direction: str
    cashflow_treatment: str
    category: str
    description: str
    counterparty_label: str | None
    external_reference: str | None
    status: str
    essential: bool
    potential_duplicate_of_id: UUID | None


class ImportErrorResponse(BaseModel):
    row_number: int
    code: str
    message: str


class ImportResponse(BaseModel):
    batch_id: UUID
    status: str
    source_sha256: str
    row_count: int
    inserted_count: int
    updated_count: int
    duplicate_count: int
    potential_duplicate_count: int
    replayed: bool
    validation_errors: list[ImportErrorResponse]


class RecurringObligationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payee_label: str = Field(min_length=1, max_length=128)
    category: str = Field(min_length=1, max_length=64)
    amount: Decimal = Field(gt=0, max_digits=18)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    frequency: Literal["WEEKLY", "FORTNIGHTLY", "MONTHLY", "QUARTERLY", "YEARLY"]
    first_due_date: date
    next_due_date: date
    due_day: int | None = Field(default=None, ge=1, le=31)
    account_id: UUID | None = None
    autopay_enabled: bool = False
    essential: bool = False


class RecurringObligationResponse(BaseModel):
    id: UUID
    account_id: UUID | None
    payee_label: str
    category: str
    amount: Decimal
    currency: str
    frequency: str
    due_day: int | None
    first_due_date: date
    next_due_date: date
    autopay_enabled: bool
    essential: bool
    status: str


class CashflowResponse(BaseModel):
    currency: str
    period_start: date
    period_end: date
    posted_transaction_count: int
    income_total: Decimal
    gross_expenses: Decimal
    refunds: Decimal
    net_expenses_after_refunds: Decimal
    essential_expenses_before_refunds: Decimal
    discretionary_expenses_before_refunds: Decimal
    net_cashflow: Decimal
    net_cashflow_to_income_percent: Decimal | None
    pending_transactions_excluded: bool
    transfer_and_ignore_treatments_excluded: bool
    savings_warning: str
