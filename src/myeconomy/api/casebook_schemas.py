"""Typed HTTP contracts for owner-private Personal Economic Casebook workflows."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from myeconomy.domain.money import currency_exponent

CaseStatusValue = Literal[
    "OPEN",
    "IN_REVIEW",
    "ACTION_READY",
    "WAITING_FOR_USER",
    "WAITING_EXTERNAL",
    "RESOLVED",
    "CLOSED",
]


class CaseFromFindingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str = Field(min_length=1, max_length=64)
    period_start: date
    period_end: date
    as_of: date
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    obligation_horizon_days: int = Field(default=30, ge=1, le=90)

    @field_validator("currency")
    @classmethod
    def validate_supported_currency(cls, value: str) -> str:
        normalized = value.upper()
        try:
            currency_exponent(normalized)
        except ValueError as exc:
            raise ValueError("Currency is not supported by the AwnNORA money kernel.") from exc
        return normalized

    @model_validator(mode="after")
    def validate_report_window(self) -> CaseFromFindingRequest:
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot precede period_start.")
        if self.period_end > self.as_of:
            raise ValueError("period_end cannot be after as_of.")
        return self


class CaseTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_status: CaseStatusValue
    expected_version: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=500)


class PersonalCaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    source_engine: str
    source_finding_id: str
    title: str
    source_snapshot: dict[str, object]
    currency: str
    amount_minor: str | None
    status: CaseStatusValue
    state_version: int
    created_at: datetime
    updated_at: datetime
    replayed: bool = False


class PersonalCaseEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    event_sequence: int
    event_type: str
    from_status: CaseStatusValue | None
    to_status: CaseStatusValue
    note: str | None
    created_at: datetime


class PersonalCaseDetailResponse(PersonalCaseResponse):
    events: list[PersonalCaseEventResponse]
