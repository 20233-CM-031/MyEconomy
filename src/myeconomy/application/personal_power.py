"""Owner-scoped Personal Mode report composition over persisted financial records."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from myeconomy.application.financial import analyze_persisted_cashflow
from myeconomy.domain.errors import FinancialDataValidationError
from myeconomy.domain.financial import minor_units_to_decimal
from myeconomy.domain.personal_power import (
    DuplicateCandidate,
    PersonalPowerInput,
    PersonalPowerReport,
    UpcomingObligation,
    build_personal_power_report,
)
from myeconomy.infrastructure.models import (
    FinancialAccount,
    FinancialTransaction,
    RecurringObligation,
)


def create_personal_power_report(
    db: Session,
    *,
    owner_user_id: UUID,
    period_start: date,
    period_end: date,
    currency: str,
    as_of: date,
    obligation_horizon_days: int = 30,
) -> PersonalPowerReport:
    """Build one private report; every query is scoped to the authenticated owner."""
    normalized_currency = currency.upper()
    if period_end > as_of:
        raise FinancialDataValidationError("Report period_end cannot be after as_of.")
    if not 1 <= obligation_horizon_days <= 90:
        raise FinancialDataValidationError("obligation_horizon_days must be between 1 and 90.")

    cashflow = analyze_persisted_cashflow(
        db,
        owner_user_id=owner_user_id,
        currency=normalized_currency,
        period_start=period_start,
        period_end=period_end,
    )
    account_count = (
        db.scalar(
            select(func.count(FinancialAccount.id)).where(
                FinancialAccount.owner_user_id == owner_user_id,
                FinancialAccount.currency == normalized_currency,
                FinancialAccount.status == "ACTIVE",
            )
        )
        or 0
    )

    duplicate_rows = db.scalars(
        select(FinancialTransaction)
        .where(
            FinancialTransaction.owner_user_id == owner_user_id,
            FinancialTransaction.currency == normalized_currency,
            FinancialTransaction.occurred_on >= period_start,
            FinancialTransaction.occurred_on <= period_end,
            FinancialTransaction.status == "POSTED",
            FinancialTransaction.potential_duplicate_of_id.is_not(None),
        )
        .order_by(FinancialTransaction.occurred_on, FinancialTransaction.id)
    ).all()
    duplicates = tuple(
        DuplicateCandidate(
            transaction_id=str(row.id),
            amount=minor_units_to_decimal(row.amount_minor, normalized_currency),
            currency=normalized_currency,
            occurred_on=row.occurred_on,
            possible_duplicate_of_id=str(row.potential_duplicate_of_id),
            description=row.description,
        )
        for row in duplicate_rows
    )

    due_end = as_of + timedelta(days=obligation_horizon_days)
    obligation_rows = db.scalars(
        select(RecurringObligation)
        .where(
            RecurringObligation.owner_user_id == owner_user_id,
            RecurringObligation.currency == normalized_currency,
            RecurringObligation.status == "ACTIVE",
            RecurringObligation.next_due_date <= due_end,
        )
        .order_by(RecurringObligation.next_due_date, RecurringObligation.id)
    ).all()
    obligations = tuple(
        UpcomingObligation(
            obligation_id=str(row.id),
            payee_label=row.payee_label,
            amount=minor_units_to_decimal(row.amount_minor, normalized_currency),
            currency=normalized_currency,
            next_due_date=row.next_due_date,
            frequency=row.frequency,
            essential=row.essential,
        )
        for row in obligation_rows
    )

    return build_personal_power_report(
        PersonalPowerInput(
            owner_reference=str(owner_user_id),
            currency=normalized_currency,
            period_start=period_start,
            period_end=period_end,
            as_of=as_of,
            account_count=int(account_count),
            posted_transaction_count=int(cashflow["posted_transaction_count"]),
            income_total=cashflow["income_total"],
            gross_expenses=cashflow["gross_expenses"],
            refunds=cashflow["refunds"],
            essential_expenses=cashflow["essential_expenses_before_refunds"],
            discretionary_expenses=cashflow["discretionary_expenses_before_refunds"],
            net_cashflow=cashflow["net_cashflow"],
            duplicate_candidates=duplicates,
            upcoming_obligations=obligations,
            obligation_horizon_days=obligation_horizon_days,
        )
    )
