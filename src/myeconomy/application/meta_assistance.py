"""Minimize a deterministic Personal Power Report for optional model assistance."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from myeconomy.application.personal_power import create_personal_power_report
from myeconomy.domain.personal_power import PersonalPowerReport

QUESTION_INTENTS = {
    "prioritize_findings": (
        "Prioritize the report findings and suggest the safest first evidence check."
    ),
    "explain_cashflow": (
        "Explain the selected-period cashflow picture using the supplied aggregates."
    ),
    "review_obligations": (
        "Explain the upcoming essential obligations and what the user should verify."
    ),
    "understand_data_gaps": "Identify missing or incomplete data that limits this report.",
}


def build_meta_safe_summary(
    report: PersonalPowerReport,
    *,
    question: str,
) -> tuple[dict[str, Any], set[str]]:
    """Build a minimized summary; user-entered payee labels and source references never cross."""
    finding_ids = {finding.finding_id for finding in report.findings[:12]}
    return (
        {
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
                "as_of": report.as_of.isoformat(),
            },
            "currency": report.currency,
            "aggregates": {
                "classified_income": str(report.income_total),
                "gross_expenses": str(report.gross_expenses),
                "refunds": str(report.refunds),
                "net_cashflow": str(report.net_cashflow),
                "essential_expenses": str(report.essential_expenses),
                "discretionary_expenses": str(report.discretionary_expenses),
                "essential_obligations_due": str(report.upcoming_essential_obligations),
                "upcoming_obligation_count": report.upcoming_obligation_count,
            },
            "findings": [
                {
                    "finding_id": item.finding_id,
                    "code": item.code,
                    "priority": item.priority,
                    # Some deterministic findings include a user-entered payee in the UI title.
                    # Replace those fields with generic wording before crossing the model boundary.
                    "title": (
                        "A recurring obligation needs review"
                        if item.code == "UPCOMING_RECURRING_OBLIGATION"
                        else item.title
                    ),
                    "explanation": (
                        "A recorded obligation falls within the selected review horizon. "
                        "Its amount and due date require confirmation with the original source."
                        if item.code == "UPCOMING_RECURRING_OBLIGATION"
                        else item.explanation
                    ),
                    "recommended_next_step": item.recommended_next_step,
                }
                for item in report.findings[:12]
            ],
            "user_question": question.strip(),
            "data_scope": "AGGREGATE_FINANCIAL_SUMMARY_AND_HOUSEHOLD_OBLIGATIONS",
            "not_included": [
                "name_or_email",
                "account_ids_or_references",
                "transaction_rows_or_identifiers",
                "counterparties_or_payees",
                "uploaded_documents_or_evidence",
                "household_member_records",
            ],
        },
        finding_ids,
    )


def create_meta_safe_summary_from_database(
    db: Session,
    *,
    owner_user_id: UUID,
    period_start: date,
    period_end: date,
    as_of: date,
    currency: str,
    question: str,
) -> tuple[dict[str, Any], set[str]]:
    report = create_personal_power_report(
        db,
        owner_user_id=owner_user_id,
        period_start=period_start,
        period_end=period_end,
        currency=currency,
        as_of=as_of,
    )
    return build_meta_safe_summary(report, question=question)
