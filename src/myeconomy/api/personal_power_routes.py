"""Owner-private Personal Mode endpoints."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from myeconomy.api.dependencies import AuthContext, require_verified_authentication
from myeconomy.api.personal_power_schemas import (
    PersonalPowerReportResponse,
    PowerFindingResponse,
)
from myeconomy.application.personal_power import create_personal_power_report
from myeconomy.infrastructure.database import get_db

router = APIRouter(prefix="/api/v1/personal", tags=["personal-mode"])


@router.get(
    "/power-report",
    response_model=PersonalPowerReportResponse,
    summary="Build a private Day-One Personal Power Report from persisted records",
)
def personal_power_report_endpoint(
    period_start: date = Query(description="First inclusive date in the cashflow review window"),
    period_end: date = Query(description="Last inclusive date in the cashflow review window"),
    currency: str = Query(default="INR", min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    as_of: date | None = Query(default=None, description="Business date for due-date review"),
    obligation_horizon_days: int = Query(default=30, ge=1, le=90),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> PersonalPowerReportResponse:
    effective_as_of = as_of or datetime.now().astimezone().date()
    report = create_personal_power_report(
        db,
        owner_user_id=auth.user.id,
        period_start=period_start,
        period_end=period_end,
        currency=currency,
        as_of=effective_as_of,
        obligation_horizon_days=obligation_horizon_days,
    )
    return PersonalPowerReportResponse(
        report_version=report.report_version,
        currency=report.currency,
        period_start=report.period_start,
        period_end=report.period_end,
        as_of=report.as_of,
        account_count=report.account_count,
        posted_transaction_count=report.posted_transaction_count,
        income_total=report.income_total,
        gross_expenses=report.gross_expenses,
        refunds=report.refunds,
        net_expenses_after_refunds=report.net_expenses_after_refunds,
        essential_expenses=report.essential_expenses,
        discretionary_expenses=report.discretionary_expenses,
        net_cashflow=report.net_cashflow,
        upcoming_essential_obligations=report.upcoming_essential_obligations,
        upcoming_obligation_count=report.upcoming_obligation_count,
        potential_duplicate_count=report.potential_duplicate_count,
        verified_value_created=report.verified_value_created,
        findings=[PowerFindingResponse.model_validate(asdict(item)) for item in report.findings],
        read_only=report.read_only,
        external_actions_taken=report.external_actions_taken,
        commons_required=report.commons_required,
        limitations=list(report.limitations),
    )
