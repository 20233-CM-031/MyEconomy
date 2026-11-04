"""Owner-private API for the Personal Economic Casebook."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from myeconomy.api.casebook_schemas import (
    CaseFromFindingRequest,
    CaseTransitionRequest,
    PersonalCaseDetailResponse,
    PersonalCaseEventResponse,
    PersonalCaseResponse,
)
from myeconomy.api.dependencies import AuthContext, require_verified_authentication
from myeconomy.application.casebook import (
    create_case_from_finding,
    get_personal_case,
    list_case_events,
    list_personal_cases,
    transition_personal_case,
)
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.models import PersonalCase, PersonalCaseEvent

router = APIRouter(prefix="/api/v1/cases", tags=["personal-casebook"])


def _case_response(item: PersonalCase, *, replayed: bool = False) -> PersonalCaseResponse:
    return PersonalCaseResponse(
        id=item.id,
        source_engine=item.source_engine,
        source_finding_id=item.source_finding_id,
        title=item.title,
        source_snapshot=item.source_snapshot,
        currency=item.currency,
        amount_minor=str(item.amount_minor) if item.amount_minor is not None else None,
        status=item.status,
        state_version=item.state_version,
        created_at=item.created_at,
        updated_at=item.updated_at,
        replayed=replayed,
    )


def _event_response(item: PersonalCaseEvent) -> PersonalCaseEventResponse:
    return PersonalCaseEventResponse(
        id=item.id,
        event_sequence=item.event_sequence,
        event_type=item.event_type,
        from_status=item.from_status,
        to_status=item.to_status,
        note=item.note,
        created_at=item.created_at,
    )


def _detail_response(
    item: PersonalCase, *, replayed: bool = False, db: Session
) -> PersonalCaseDetailResponse:
    base = _case_response(item, replayed=replayed)
    return PersonalCaseDetailResponse(
        **base.model_dump(),
        events=[_event_response(event) for event in list_case_events(db, case_id=item.id)],
    )


@router.post(
    "/from-finding",
    response_model=PersonalCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a personal case from a current server-computed Power Report finding",
)
def open_case_from_finding(
    payload: CaseFromFindingRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> PersonalCaseResponse:
    item, replayed = create_case_from_finding(
        db,
        owner_user_id=auth.user.id,
        finding_id=payload.finding_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        as_of=payload.as_of,
        currency=payload.currency,
        obligation_horizon_days=payload.obligation_horizon_days,
        idempotency_key=idempotency_key,
    )
    return _case_response(item, replayed=replayed)


@router.get(
    "",
    response_model=list[PersonalCaseResponse],
    summary="List the authenticated user's cases",
)
def list_cases(
    limit: int = Query(default=50, ge=1, le=100),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[PersonalCaseResponse]:
    items = list_personal_cases(db, owner_user_id=auth.user.id, limit=limit)
    return [_case_response(item) for item in items]


@router.get(
    "/{case_id}",
    response_model=PersonalCaseDetailResponse,
    summary="Read a case and its immutable timeline",
)
def get_case_detail(
    case_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> PersonalCaseDetailResponse:
    item = get_personal_case(db, owner_user_id=auth.user.id, case_id=case_id)
    return _detail_response(item, db=db)


@router.post(
    "/{case_id}/transition",
    response_model=PersonalCaseDetailResponse,
    summary="Move a case using a version precondition and idempotency key",
)
def transition_case(
    case_id: UUID,
    payload: CaseTransitionRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> PersonalCaseDetailResponse:
    item, replayed = transition_personal_case(
        db,
        owner_user_id=auth.user.id,
        case_id=case_id,
        to_status=payload.to_status,
        expected_version=payload.expected_version,
        idempotency_key=idempotency_key,
        note=payload.note,
    )
    return _detail_response(item, replayed=replayed, db=db)
