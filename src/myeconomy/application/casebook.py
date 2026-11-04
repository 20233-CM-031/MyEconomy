"""Owner-scoped casebook use cases with idempotency and optimistic concurrency."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.application.personal_power import create_personal_power_report
from myeconomy.domain.casebook import (
    CaseTransitionError,
    PersonalCaseStatus,
    transition_case_status,
)
from myeconomy.domain.errors import (
    ConflictError,
    FinancialDataValidationError,
    IdempotencyConflictError,
    NotFoundError,
)
from myeconomy.domain.financial import amount_to_minor_units
from myeconomy.infrastructure.models import PersonalCase, PersonalCaseEvent, utc_now


def _canonical_hash(value: dict[str, object]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def _finding_snapshot(
    finding: object, *, period_start: date, period_end: date, as_of: date
) -> dict[str, object]:
    """Freeze the finding as computed by the server; the client never supplies its facts."""
    amount = finding.amount
    return {
        "finding_id": finding.finding_id,
        "code": finding.code,
        "priority": finding.priority,
        "title": finding.title,
        "explanation": finding.explanation,
        "recommended_next_step": finding.recommended_next_step,
        "amount": str(amount) if amount is not None else None,
        "currency": finding.currency,
        "source_references": list(finding.source_references),
        "value_status": finding.value_status,
        "report_period": {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "as_of": as_of.isoformat(),
        },
        "origin": "SERVER_COMPUTED_PERSONAL_POWER_REPORT",
    }


def _case_identity(
    *, finding_id: str, period_start: date, period_end: date, as_of: date, currency: str
) -> dict[str, object]:
    return {
        "source_engine": "PERSONAL",
        "source_finding_id": finding_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "as_of": as_of.isoformat(),
        "currency": currency.upper(),
    }


def create_case_from_finding(
    db: Session,
    *,
    owner_user_id: UUID,
    finding_id: str,
    period_start: date,
    period_end: date,
    as_of: date,
    currency: str,
    obligation_horizon_days: int,
    idempotency_key: str,
) -> tuple[PersonalCase, bool]:
    """Create a case from a current server-side finding, or replay its prior case."""
    if not idempotency_key.strip() or len(idempotency_key) > 128:
        raise FinancialDataValidationError("Idempotency-Key must contain 1 to 128 characters.")
    normalized_currency = currency.upper()
    if len(finding_id) > 64 or not finding_id.strip():
        raise FinancialDataValidationError("A valid finding_id is required.")

    identity = _case_identity(
        finding_id=finding_id,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of,
        currency=normalized_currency,
    )
    request_hash = _canonical_hash({**identity, "obligation_horizon_days": obligation_horizon_days})

    prior_by_key = db.scalar(
        select(PersonalCase).where(
            PersonalCase.owner_user_id == owner_user_id,
            PersonalCase.idempotency_key == idempotency_key,
        )
    )
    if prior_by_key is not None:
        if prior_by_key.request_sha256 != request_hash:
            raise IdempotencyConflictError(
                "This case creation key was already used with different report parameters."
            )
        return prior_by_key, True

    report = create_personal_power_report(
        db,
        owner_user_id=owner_user_id,
        period_start=period_start,
        period_end=period_end,
        currency=normalized_currency,
        as_of=as_of,
        obligation_horizon_days=obligation_horizon_days,
    )
    finding = next((item for item in report.findings if item.finding_id == finding_id), None)
    if finding is None:
        raise NotFoundError(
            "The finding is no longer present in the selected report. Refresh it and try again."
        )

    source_snapshot = _finding_snapshot(
        finding, period_start=period_start, period_end=period_end, as_of=as_of
    )
    natural_match = db.scalar(
        select(PersonalCase).where(
            PersonalCase.owner_user_id == owner_user_id,
            PersonalCase.source_engine == "PERSONAL",
            PersonalCase.source_finding_id == finding_id,
            PersonalCase.period_start == period_start,
            PersonalCase.period_end == period_end,
            PersonalCase.as_of == as_of,
            PersonalCase.currency == normalized_currency,
        )
    )
    if natural_match is not None:
        if natural_match.source_snapshot != source_snapshot:
            raise ConflictError(
                "A case already exists for this finding, but its source snapshot differs."
            )
        return natural_match, True

    amount_minor: int | None = None
    if finding.amount is not None:
        try:
            amount_minor = amount_to_minor_units(
                Decimal(str(finding.amount)), normalized_currency, allow_zero=True
            )
        except ValueError as exc:
            raise FinancialDataValidationError(
                "The finding amount is invalid for its currency."
            ) from exc

    case = PersonalCase(
        id=uuid4(),
        owner_user_id=owner_user_id,
        source_engine="PERSONAL",
        source_finding_id=finding.finding_id,
        idempotency_key=idempotency_key,
        request_sha256=request_hash,
        period_start=period_start,
        period_end=period_end,
        as_of=as_of,
        currency=normalized_currency,
        amount_minor=amount_minor,
        title=finding.title,
        source_snapshot=source_snapshot,
        status=PersonalCaseStatus.OPEN.value,
        state_version=1,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(case)
    db.add(
        PersonalCaseEvent(
            id=uuid4(),
            case_id=case.id,
            actor_user_id=owner_user_id,
            event_sequence=1,
            event_type="CASE_OPENED",
            from_status=None,
            to_status=PersonalCaseStatus.OPEN.value,
            note="Case opened from a server-computed Personal Power finding.",
            idempotency_key=f"open:{sha256(idempotency_key.encode('utf-8')).hexdigest()}",
            request_sha256=request_hash,
            created_at=utc_now(),
        )
    )
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="personal_case.opened",
        subject_type="personal_case",
        subject_id=str(case.id),
        details={
            "source_engine": "PERSONAL",
            "source_finding_id": finding.finding_id,
            "status": PersonalCaseStatus.OPEN.value,
            "source_period_start": period_start.isoformat(),
            "source_period_end": period_end.isoformat(),
        },
    )
    try:
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        prior_by_key = db.scalar(
            select(PersonalCase).where(
                PersonalCase.owner_user_id == owner_user_id,
                PersonalCase.idempotency_key == idempotency_key,
            )
        )
        if prior_by_key is not None and prior_by_key.request_sha256 == request_hash:
            return prior_by_key, True
        natural_match = db.scalar(
            select(PersonalCase).where(
                PersonalCase.owner_user_id == owner_user_id,
                PersonalCase.source_engine == "PERSONAL",
                PersonalCase.source_finding_id == finding_id,
                PersonalCase.period_start == period_start,
                PersonalCase.period_end == period_end,
                PersonalCase.as_of == as_of,
                PersonalCase.currency == normalized_currency,
            )
        )
        if natural_match is not None and natural_match.source_snapshot == source_snapshot:
            return natural_match, True
        raise ConflictError(
            "A concurrent request created or changed this case. Refresh and retry."
        ) from None
    db.refresh(case)
    return case, False


def list_personal_cases(db: Session, *, owner_user_id: UUID, limit: int = 50) -> list[PersonalCase]:
    return list(
        db.scalars(
            select(PersonalCase)
            .where(PersonalCase.owner_user_id == owner_user_id)
            .order_by(PersonalCase.updated_at.desc(), PersonalCase.id)
            .limit(limit)
        ).all()
    )


def get_personal_case(db: Session, *, owner_user_id: UUID, case_id: UUID) -> PersonalCase:
    item = db.scalar(
        select(PersonalCase).where(
            PersonalCase.id == case_id,
            PersonalCase.owner_user_id == owner_user_id,
        )
    )
    if item is None:
        raise NotFoundError("Personal case was not found.")
    return item


def list_case_events(db: Session, *, case_id: UUID) -> list[PersonalCaseEvent]:
    return list(
        db.scalars(
            select(PersonalCaseEvent)
            .where(PersonalCaseEvent.case_id == case_id)
            .order_by(PersonalCaseEvent.event_sequence)
        ).all()
    )


def transition_personal_case(
    db: Session,
    *,
    owner_user_id: UUID,
    case_id: UUID,
    to_status: str,
    expected_version: int,
    idempotency_key: str,
    note: str | None = None,
) -> tuple[PersonalCase, bool]:
    """Move a case with a version precondition; no provider or payment side effect occurs."""
    if not idempotency_key.strip() or len(idempotency_key) > 128:
        raise FinancialDataValidationError("Idempotency-Key must contain 1 to 128 characters.")
    if expected_version < 1:
        raise FinancialDataValidationError("expected_version must be at least 1.")
    cleaned_note = " ".join((note or "").split())[:500] or None
    request_hash = _canonical_hash(
        {
            "to_status": to_status,
            "expected_version": expected_version,
            "note": cleaned_note,
        }
    )
    item = get_personal_case(db, owner_user_id=owner_user_id, case_id=case_id)
    prior_event = db.scalar(
        select(PersonalCaseEvent).where(
            PersonalCaseEvent.case_id == case_id,
            PersonalCaseEvent.idempotency_key == idempotency_key,
        )
    )
    if prior_event is not None:
        if prior_event.request_sha256 != request_hash:
            raise IdempotencyConflictError(
                "This transition key was already used with different case state."
            )
        return item, True

    if item.state_version != expected_version:
        raise ConflictError(
            "This case changed since it was opened. "
            f"Current version is {item.state_version}; refresh before updating."
        )
    try:
        next_status = transition_case_status(item.status, to_status)
    except CaseTransitionError as exc:
        raise FinancialDataValidationError(str(exc)) from exc

    previous_status = item.status
    next_version = item.state_version + 1
    # Version-qualified UPDATE provides compare-and-set semantics even when two
    # SQLite requests race; PostgreSQL additionally locks the row via its UPDATE.
    from sqlalchemy import update

    result = db.execute(
        update(PersonalCase)
        .where(
            PersonalCase.id == case_id,
            PersonalCase.owner_user_id == owner_user_id,
            PersonalCase.state_version == expected_version,
        )
        .values(
            status=next_status.value,
            state_version=next_version,
            updated_at=utc_now(),
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raced_event = db.scalar(
            select(PersonalCaseEvent).where(
                PersonalCaseEvent.case_id == case_id,
                PersonalCaseEvent.idempotency_key == idempotency_key,
            )
        )
        if raced_event is not None:
            if raced_event.request_sha256 != request_hash:
                raise IdempotencyConflictError(
                    "This transition key was already used with different case state."
                )
            return get_personal_case(db, owner_user_id=owner_user_id, case_id=case_id), True
        raise ConflictError(
            "This case was updated by another request. Refresh before trying again."
        )

    db.add(
        PersonalCaseEvent(
            id=uuid4(),
            case_id=case_id,
            actor_user_id=owner_user_id,
            event_sequence=next_version,
            event_type="STATUS_CHANGED",
            from_status=previous_status,
            to_status=next_status.value,
            note=cleaned_note,
            idempotency_key=idempotency_key,
            request_sha256=request_hash,
            created_at=utc_now(),
        )
    )
    record_audit_event(
        db,
        actor_user_id=owner_user_id,
        action="personal_case.status_changed",
        subject_type="personal_case",
        subject_id=str(case_id),
        details={
            "from_status": previous_status,
            "to_status": next_status.value,
            "state_version": next_version,
        },
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        prior_event = db.scalar(
            select(PersonalCaseEvent).where(
                PersonalCaseEvent.case_id == case_id,
                PersonalCaseEvent.idempotency_key == idempotency_key,
            )
        )
        if prior_event is not None and prior_event.request_sha256 == request_hash:
            return get_personal_case(db, owner_user_id=owner_user_id, case_id=case_id), True
        raise ConflictError(
            "A concurrent case update won. Refresh the case before retrying."
        ) from None
    return get_personal_case(db, owner_user_id=owner_user_id, case_id=case_id), False
