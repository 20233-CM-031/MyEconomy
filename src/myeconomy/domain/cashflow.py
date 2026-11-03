"""Deterministic household cashflow calculation rules."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from myeconomy.domain.money import quantize_amount, quantize_total


@dataclass(frozen=True, slots=True)
class CashflowEntry:
    occurred_on: date
    amount: Decimal
    category: str
    essential: bool = False


@dataclass(frozen=True, slots=True)
class CategoryTotal:
    category: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CashflowSummary:
    currency: str
    period_start: date
    period_end: date
    income_total: Decimal
    expense_total: Decimal
    net_cashflow: Decimal
    essential_expenses: Decimal
    discretionary_expenses: Decimal
    savings_rate_percent: Decimal | None
    expense_by_category: tuple[CategoryTotal, ...]


def _validate_entries(
    entries: Iterable[CashflowEntry],
    *,
    period_start: date,
    period_end: date,
    currency: str,
) -> tuple[CashflowEntry, ...]:
    validated: list[CashflowEntry] = []
    for entry in entries:
        if not period_start <= entry.occurred_on <= period_end:
            raise ValueError(
                f"Entry date {entry.occurred_on.isoformat()} is outside the requested period"
            )
        amount = quantize_amount(entry.amount, currency)
        category = entry.category.strip()
        if not category:
            raise ValueError("Category must not be empty")
        validated.append(
            CashflowEntry(
                occurred_on=entry.occurred_on,
                amount=amount,
                category=category,
                essential=entry.essential,
            )
        )
    return tuple(validated)


def analyze_cashflow(
    *,
    currency: str,
    period_start: date,
    period_end: date,
    incomes: Iterable[CashflowEntry],
    expenses: Iterable[CashflowEntry],
) -> CashflowSummary:
    """Calculate a period summary from caller-provided entries.

    This is arithmetic, not financial advice. A net surplus is not automatically
    savings: omitted cash movements, debt principal, transfers or opening balances
    can materially change a household's actual position.
    """
    normalized_currency = currency.upper()
    if period_end < period_start:
        raise ValueError("period_end must be on or after period_start")

    income_entries = _validate_entries(
        incomes,
        period_start=period_start,
        period_end=period_end,
        currency=normalized_currency,
    )
    expense_entries = _validate_entries(
        expenses,
        period_start=period_start,
        period_end=period_end,
        currency=normalized_currency,
    )

    income_total = quantize_total(
        sum((item.amount for item in income_entries), start=Decimal("0")),
        normalized_currency,
    )
    expense_total = quantize_total(
        sum((item.amount for item in expense_entries), start=Decimal("0")),
        normalized_currency,
    )
    essential_total = quantize_total(
        sum(
            (item.amount for item in expense_entries if item.essential),
            start=Decimal("0"),
        ),
        normalized_currency,
    )
    discretionary_total = quantize_total(
        expense_total - essential_total,
        normalized_currency,
    )
    net_cashflow = quantize_total(income_total - expense_total, normalized_currency)
    savings_rate = (
        (net_cashflow / income_total * Decimal("100")).quantize(Decimal("0.01"))
        if income_total > 0
        else None
    )

    category_totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in expense_entries:
        category_totals[item.category] += item.amount
    sorted_categories = tuple(
        CategoryTotal(
            category=category,
            amount=quantize_total(amount, normalized_currency),
        )
        for category, amount in sorted(
            category_totals.items(), key=lambda pair: (-pair[1], pair[0].casefold())
        )
    )

    return CashflowSummary(
        currency=normalized_currency,
        period_start=period_start,
        period_end=period_end,
        income_total=income_total,
        expense_total=expense_total,
        net_cashflow=net_cashflow,
        essential_expenses=essential_total,
        discretionary_expenses=discretionary_total,
        savings_rate_percent=savings_rate,
        expense_by_category=sorted_categories,
    )
