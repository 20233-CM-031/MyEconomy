"""Purpose-consented, read-only Meta explanation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from myeconomy.api.dependencies import AuthContext, require_verified_authentication
from myeconomy.api.meta_assistance_schemas import (
    PersonalExplanationRequest,
    PersonalExplanationResponse,
)
from myeconomy.application.audit import record_audit_event
from myeconomy.application.consents import require_active_consent
from myeconomy.application.meta_assistance import (
    QUESTION_INTENTS,
    create_meta_safe_summary_from_database,
)
from myeconomy.domain.consent import ConsentPurpose, DataCategory, RecipientType
from myeconomy.domain.errors import ServiceUnavailableError
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.meta_model_api import MetaModelUnavailable, call_personal_explanation

router = APIRouter(prefix="/api/v1/intelligence", tags=["meta-model-assistance"])


@router.post(
    "/personal-explanation",
    response_model=PersonalExplanationResponse,
    summary="Explain a private deterministic report using Muse Spark Standard mode",
)
def explain_personal_report(
    payload: PersonalExplanationRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> PersonalExplanationResponse:
    # Consent is checked in this request's DB session before owner-scoped facts are read.
    for category in (DataCategory.FINANCIAL_SUMMARY, DataCategory.HOUSEHOLD_OBLIGATIONS):
        require_active_consent(
            db,
            subject_user_id=auth.user.id,
            purpose=ConsentPurpose.AI_ASSISTANCE,
            category=category,
            recipient_type=RecipientType.SERVICE,
            recipient_id="meta-model-api",
        )
    summary, finding_ids = create_meta_safe_summary_from_database(
        db,
        owner_user_id=auth.user.id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        as_of=payload.as_of,
        currency=payload.currency,
        question=QUESTION_INTENTS[payload.question_intent],
    )
    record_audit_event(
        db,
        actor_user_id=auth.user.id,
        action="intelligence.meta_explanation.requested",
        subject_type="personal_power_report",
        subject_id=None,
        details={
            "model": "muse-spark-1.3",
            "mode": "STANDARD",
            "scope": "AGGREGATE_FINANCIAL_SUMMARY_AND_OBLIGATIONS_ONLY",
            "period_start": payload.period_start.isoformat(),
            "period_end": payload.period_end.isoformat(),
            "currency": payload.currency,
            "external_mutation": False,
        },
    )
    # Commit the authorization/read snapshot and redacted request audit before the network call.
    # Do not hold a database connection or transaction open while waiting on the model API.
    db.commit()
    try:
        result = call_personal_explanation(
            question=QUESTION_INTENTS[payload.question_intent],
            personal_summary=summary,
            allowed_finding_ids=finding_ids,
        )
    except MetaModelUnavailable as exc:
        raise ServiceUnavailableError(str(exc)) from exc
    record_audit_event(
        db,
        actor_user_id=auth.user.id,
        action="intelligence.meta_explanation.completed",
        subject_type="personal_power_report",
        details={
            "model": result["model"],
            "mode": result["mode"],
            "action_count": len(result["actions"]),
            "external_mutation": False,
        },
    )
    db.commit()
    return PersonalExplanationResponse.model_validate(result)
