"""Central append-only audit-event helper. Never pass secrets or raw documents here."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from myeconomy.infrastructure.models import AuditEvent


def record_audit_event(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action: str,
    subject_type: str,
    subject_id: str | None = None,
    household_id: UUID | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_user_id=actor_user_id,
            household_id=household_id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            details=details or {},
        )
    )
