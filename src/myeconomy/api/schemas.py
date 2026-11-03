"""Validated API request and response contracts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from myeconomy.domain.money import MoneyInputError, quantize_amount

Category = Annotated[str, Field(min_length=1, max_length=64)]


class CashflowEntryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_on: date
    amount: Decimal = Field(gt=0, max_digits=18)
    category: Category
    essential: bool = False

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Category must not be empty")
        return normalized


class CashflowAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    period_start: date
    period_end: date
    incomes: list[CashflowEntryInput] = Field(default_factory=list, max_length=5000)
    expenses: list[CashflowEntryInput] = Field(default_factory=list, max_length=5000)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.upper()
        # Reuse the domain's supported-currency registry at the boundary.
        from myeconomy.domain.money import currency_exponent

        try:
            currency_exponent(normalized)
        except MoneyInputError as exc:
            raise ValueError(str(exc)) from exc
        return normalized

    @model_validator(mode="after")
    def validate_period_and_precision(self) -> CashflowAnalysisRequest:
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        for item in [*self.incomes, *self.expenses]:
            if not self.period_start <= item.occurred_on <= self.period_end:
                raise ValueError(
                    f"Entry date {item.occurred_on.isoformat()} is outside the requested period"
                )
            try:
                quantize_amount(item.amount, self.currency)
            except MoneyInputError as exc:
                raise ValueError(str(exc)) from exc
        return self


class CategoryTotalResponse(BaseModel):
    category: str
    amount: Decimal


class CashflowAnalysisResponse(BaseModel):
    currency: str
    period_start: date
    period_end: date
    income_total: Decimal
    expense_total: Decimal
    net_cashflow: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    savings_rate_percent: Decimal | None
    expense_by_category: list[CategoryTotalResponse]
    calculation_note: str = (
        "Net cashflow is calculated only from the entries supplied. It is not a verified "
        "bank balance or a complete measure of savings."
    )
