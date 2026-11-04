"""Typed HTTP response contracts for the Personal Mode Power Report."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PowerFindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    code: str
    priority: str
    title: str
    explanation: str
    recommended_next_step: str
    amount: Decimal | None
    currency: str | None
    source_references: list[str]
    value_status: str


class PersonalPowerReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_version: str
    currency: str
    period_start: date
    period_end: date
    as_of: date
    account_count: int
    posted_transaction_count: int
    income_total: Decimal
    gross_expenses: Decimal
    refunds: Decimal
    net_expenses_after_refunds: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    net_cashflow: Decimal
    upcoming_essential_obligations: Decimal
    upcoming_obligation_count: int
    potential_duplicate_count: int
    verified_value_created: Decimal
    findings: list[PowerFindingResponse]
    read_only: bool
    external_actions_taken: bool
    commons_required: bool
    limitations: list[str]
