"""Contracts for consent-gated Meta explanation requests."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

QuestionIntent = Literal[
    "prioritize_findings", "explain_cashflow", "review_obligations", "understand_data_gaps"
]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$", min_length=3, max_length=3)]


class PersonalExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_start: date
    period_end: date
    as_of: date
    currency: Currency = "INR"
    question_intent: QuestionIntent

    @model_validator(mode="after")
    def validate_period(self) -> PersonalExplanationRequest:
        if self.period_end < self.period_start:
            raise ValueError("period_end must not precede period_start.")
        if self.period_end > self.as_of:
            raise ValueError("period_end must not be after as_of.")
        if (self.period_end - self.period_start) > timedelta(days=365):
            raise ValueError("The Meta explanation window cannot exceed 365 days.")
        return self


class ExplanationAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    why_it_matters: str
    next_step: str
    uncertainty: str


class PersonalExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    actions: list[ExplanationAction]
    limitations: list[str]
    model: Literal["muse-spark-1.3"]
    mode: Literal["STANDARD"]
    external_actions_taken: Literal[False] = False
