"""Cashflow analysis application use case."""

from __future__ import annotations

from datetime import date

from myeconomy.domain.cashflow import CashflowEntry, CashflowSummary, analyze_cashflow


def run_cashflow_analysis(
    *,
    currency: str,
    period_start: date,
    period_end: date,
    incomes: list[CashflowEntry],
    expenses: list[CashflowEntry],
) -> CashflowSummary:
    return analyze_cashflow(
        currency=currency,
        period_start=period_start,
        period_end=period_end,
        incomes=incomes,
        expenses=expenses,
    )
