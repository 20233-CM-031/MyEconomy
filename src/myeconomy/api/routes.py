"""Versioned HTTP routes."""

from fastapi import APIRouter

from myeconomy.api.schemas import (
    CashflowAnalysisRequest,
    CashflowAnalysisResponse,
    CategoryTotalResponse,
)
from myeconomy.application.cashflow import run_cashflow_analysis
from myeconomy.domain.cashflow import CashflowEntry

router = APIRouter(prefix="/api/v1")


@router.post(
    "/cashflow/analyze",
    response_model=CashflowAnalysisResponse,
    summary="Analyze caller-provided income and expense entries",
)
def analyze_cashflow_endpoint(payload: CashflowAnalysisRequest) -> CashflowAnalysisResponse:
    summary = run_cashflow_analysis(
        currency=payload.currency,
        period_start=payload.period_start,
        period_end=payload.period_end,
        incomes=[
            CashflowEntry(
                occurred_on=item.occurred_on,
                amount=item.amount,
                category=item.category,
            )
            for item in payload.incomes
        ],
        expenses=[
            CashflowEntry(
                occurred_on=item.occurred_on,
                amount=item.amount,
                category=item.category,
                essential=item.essential,
            )
            for item in payload.expenses
        ],
    )
    return CashflowAnalysisResponse(
        currency=summary.currency,
        period_start=summary.period_start,
        period_end=summary.period_end,
        income_total=summary.income_total,
        expense_total=summary.expense_total,
        net_cashflow=summary.net_cashflow,
        essential_expenses=summary.essential_expenses,
        discretionary_expenses=summary.discretionary_expenses,
        savings_rate_percent=summary.savings_rate_percent,
        expense_by_category=[
            CategoryTotalResponse(category=item.category, amount=item.amount)
            for item in summary.expense_by_category
        ],
    )
