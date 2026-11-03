"""Purpose-bound consent creation, lookup and immediate revocation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.application.households import require_household_membership
from myeconomy.domain.consent import (
    ConsentPurpose,
    DataCategory,
    RecipientType,
    get_consent_terms,
    validate_consent_scope,
)
from myeconomy.domain.errors import ConsentRequiredError, ConsentScopeError, NotFoundError
from myeconomy.infrastructure.models import ConsentGrant, User

DEFAULT_CONSENT_TTL = timedelta(days=90)
MAX_CONSENT_TTL = timedelta(days=365)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def effective_status(grant: ConsentGrant, *, now: datetime | None = None) -> str:
    if grant.status == "revoked":
        return "revoked"
    current = now or datetime.now(UTC)
    if _utc(grant.expires_at) <= current:
        return "expired"
    return "active"


def create_consent(
    db: Session,
    *,
    subject: User,
    purpose: ConsentPurpose,
    categories: list[DataCategory],
    recipient_type: RecipientType,
    recipient_id: str,
    terms_version: str,
    expires_at: datetime | None,
) -> ConsentGrant:
    current_terms = get_consent_terms(purpose)
    if terms_version != current_terms.version:
        raise ConsentScopeError(
            f"The consent terms changed. Review and accept version '{current_terms.version}'."
        )
    validate_consent_scope(
        purpose=purpose,
        categories=categories,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
    )
    now = datetime.now(UTC)
    expiry = _utc(expires_at) if expires_at else now + DEFAULT_CONSENT_TTL
    if expiry <= now + timedelta(minutes=1) or expiry > now + MAX_CONSENT_TTL:
        raise ConsentScopeError(
            "Consent expiry must be more than one minute and no more than 365 days away."
        )

    if recipient_type == RecipientType.HOUSEHOLD:
        try:
            household_id = UUID(recipient_id)
        except ValueError as exc:
            raise ConsentScopeError(
                "Household recipient_id must be a valid household UUID."
            ) from exc
        require_household_membership(db, user_id=subject.id, household_id=household_id)

    grant = ConsentGrant(
        subject_user_id=subject.id,
        purpose=purpose.value,
        data_categories=sorted(category.value for category in set(categories)),
        recipient_type=recipient_type.value,
        recipient_id=recipient_id.strip(),
        terms_version=terms_version.strip(),
        status="active",
        granted_at=now,
        expires_at=expiry,
    )
    db.add(grant)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=subject.id,
        action="consent.granted",
        subject_type="consent_grant",
        subject_id=str(grant.id),
        details={
            "purpose": purpose.value,
            "data_categories": grant.data_categories,
            "recipient_type": recipient_type.value,
            "recipient_id": grant.recipient_id,
            "terms_version": grant.terms_version,
            "expires_at": expiry.isoformat(),
        },
    )
    db.commit()
    db.refresh(grant)
    return grant


def list_consents(db: Session, *, subject_user_id: UUID) -> list[ConsentGrant]:
    return list(
        db.scalars(
            select(ConsentGrant)
            .where(ConsentGrant.subject_user_id == subject_user_id)
            .order_by(ConsentGrant.granted_at.desc())
        ).all()
    )


def revoke_consent(db: Session, *, subject: User, consent_id: UUID) -> ConsentGrant:
    grant = db.scalar(
        select(ConsentGrant).where(
            ConsentGrant.id == consent_id,
            ConsentGrant.subject_user_id == subject.id,
        )
    )
    if grant is None:
        raise NotFoundError("Consent grant was not found.")
    if grant.status != "revoked":
        grant.status = "revoked"
        grant.revoked_at = datetime.now(UTC)
        record_audit_event(
            db,
            actor_user_id=subject.id,
            action="consent.revoked",
            subject_type="consent_grant",
            subject_id=str(grant.id),
            details={"purpose": grant.purpose, "recipient_type": grant.recipient_type},
        )
        db.commit()
        db.refresh(grant)
    return grant


def has_active_consent(
    db: Session,
    *,
    subject_user_id: UUID,
    purpose: ConsentPurpose,
    category: DataCategory,
    recipient_type: RecipientType,
    recipient_id: str,
    now: datetime | None = None,
) -> bool:
    current = now or datetime.now(UTC)
    grants = db.scalars(
        select(ConsentGrant).where(
            ConsentGrant.subject_user_id == subject_user_id,
            ConsentGrant.purpose == purpose.value,
            ConsentGrant.recipient_type == recipient_type.value,
            ConsentGrant.recipient_id == recipient_id,
            ConsentGrant.status == "active",
        )
    ).all()
    return any(
        category.value in grant.data_categories and _utc(grant.expires_at) > current
        for grant in grants
    )


def require_active_consent(
    db: Session,
    *,
    subject_user_id: UUID,
    purpose: ConsentPurpose,
    category: DataCategory,
    recipient_type: RecipientType,
    recipient_id: str,
    now: datetime | None = None,
) -> None:
    """Enforce consent inside the same application transaction as future data access."""
    if not has_active_consent(
        db,
        subject_user_id=subject_user_id,
        purpose=purpose,
        category=category,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        now=now,
    ):
        raise ConsentRequiredError()
