"""Household membership use cases, invitations and resource-level authorization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.application.identity import normalize_email
from myeconomy.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from myeconomy.infrastructure.models import (
    Household,
    HouseholdInvitation,
    HouseholdMembership,
    User,
)
from myeconomy.infrastructure.security import hash_session_token, issue_session_token

INVITATION_TTL = timedelta(hours=72)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def require_household_membership(
    db: Session, *, user_id: UUID, household_id: UUID
) -> HouseholdMembership:
    membership = db.scalar(
        select(HouseholdMembership).where(
            HouseholdMembership.household_id == household_id,
            HouseholdMembership.user_id == user_id,
        )
    )
    # Do not reveal whether a household exists to a non-member.
    if membership is None:
        raise NotFoundError("Household was not found.")
    return membership


def create_household(db: Session, *, owner: User, name: str) -> Household:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Household name must not be empty.")
    household = Household(name=normalized_name, created_by_user_id=owner.id)
    db.add(household)
    db.flush()
    db.add(
        HouseholdMembership(
            household_id=household.id,
            user_id=owner.id,
            role="owner",
        )
    )
    record_audit_event(
        db,
        actor_user_id=owner.id,
        action="household.created",
        subject_type="household",
        subject_id=str(household.id),
        household_id=household.id,
        details={"owner_membership_created": True},
    )
    db.commit()
    db.refresh(household)
    return household


def list_households(db: Session, *, user_id: UUID) -> list[tuple[Household, str]]:
    rows = db.execute(
        select(Household, HouseholdMembership.role)
        .join(HouseholdMembership, HouseholdMembership.household_id == Household.id)
        .where(HouseholdMembership.user_id == user_id)
        .order_by(Household.created_at, Household.name)
    ).all()
    return [(household, role) for household, role in rows]


def create_household_invitation(
    db: Session,
    *,
    actor: User,
    household_id: UUID,
    invited_email: str,
) -> tuple[HouseholdInvitation, str]:
    membership = require_household_membership(db, user_id=actor.id, household_id=household_id)
    if membership.role != "owner":
        raise AuthorizationError("Only a household owner can invite members in this iteration.")

    normalized_email = normalize_email(invited_email)
    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        existing_membership = db.scalar(
            select(HouseholdMembership).where(
                HouseholdMembership.household_id == household_id,
                HouseholdMembership.user_id == existing_user.id,
            )
        )
        if existing_membership is not None:
            raise ConflictError("This person is already a household member.")

    raw_token = issue_session_token()
    now = datetime.now(UTC)
    prior = db.scalar(
        select(HouseholdInvitation)
        .where(
            HouseholdInvitation.household_id == household_id,
            HouseholdInvitation.invited_email == normalized_email,
            HouseholdInvitation.accepted_at.is_(None),
            HouseholdInvitation.revoked_at.is_(None),
        )
        .with_for_update()
    )
    if prior is not None and _utc(prior.expires_at) > now:
        raise ConflictError("An active invitation already exists for this email.")
    if prior is not None:
        prior.revoked_at = now

    invitation = HouseholdInvitation(
        household_id=household_id,
        invited_email=normalized_email,
        token_hash=hash_session_token(raw_token),
        invited_by_user_id=actor.id,
        created_at=now,
        expires_at=now + INVITATION_TTL,
    )
    db.add(invitation)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("An active invitation already exists for this email.") from exc
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action="household.invitation_created",
        subject_type="household_invitation",
        subject_id=str(invitation.id),
        household_id=household_id,
        details={"expires_at": invitation.expires_at.isoformat()},
    )
    db.commit()
    db.refresh(invitation)
    return invitation, raw_token


def accept_household_invitation(db: Session, *, actor: User, raw_token: str) -> HouseholdMembership:
    invitation = db.scalar(
        select(HouseholdInvitation)
        .where(HouseholdInvitation.token_hash == hash_session_token(raw_token))
        .with_for_update()
    )
    now = datetime.now(UTC)
    if invitation is None:
        raise NotFoundError("A valid household invitation was not found.")
    if (
        invitation.revoked_at is not None
        or invitation.accepted_at is not None
        or _utc(invitation.expires_at) <= now
    ):
        raise ConflictError("This household invitation is no longer active.")
    if invitation.invited_email != normalize_email(actor.email):
        # Keep the invitation unusable by a different signed-in account.
        raise AuthenticationError("This invitation belongs to a different email account.")

    membership = HouseholdMembership(
        household_id=invitation.household_id,
        user_id=actor.id,
        role="member",
    )
    invitation.accepted_at = now
    db.add(membership)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("This account is already a member of the household.") from exc

    record_audit_event(
        db,
        actor_user_id=actor.id,
        action="household.invitation_accepted",
        subject_type="household_invitation",
        subject_id=str(invitation.id),
        household_id=invitation.household_id,
        details={"role": "member"},
    )
    db.commit()
    db.refresh(membership)
    return membership


def revoke_household_invitation(
    db: Session, *, actor: User, invitation_id: UUID
) -> HouseholdInvitation:
    invitation = db.get(HouseholdInvitation, invitation_id)
    if invitation is None:
        raise NotFoundError("Household invitation was not found.")
    membership = require_household_membership(
        db, user_id=actor.id, household_id=invitation.household_id
    )
    if membership.role != "owner":
        raise AuthorizationError("Only a household owner can revoke invitations.")
    if invitation.accepted_at is not None:
        raise ConflictError("An accepted invitation cannot be revoked.")
    if invitation.revoked_at is None:
        invitation.revoked_at = datetime.now(UTC)
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action="household.invitation_revoked",
            subject_type="household_invitation",
            subject_id=str(invitation.id),
            household_id=invitation.household_id,
        )
        db.commit()
        db.refresh(invitation)
    return invitation


def list_household_members(
    db: Session, *, actor: User, household_id: UUID
) -> list[tuple[HouseholdMembership, User]]:
    require_household_membership(db, user_id=actor.id, household_id=household_id)
    rows = db.execute(
        select(HouseholdMembership, User)
        .join(User, User.id == HouseholdMembership.user_id)
        .where(HouseholdMembership.household_id == household_id)
        .order_by(HouseholdMembership.created_at)
    ).all()
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action="household.members_listed",
        subject_type="household",
        subject_id=str(household_id),
        household_id=household_id,
        details={"member_count": len(rows)},
    )
    db.commit()
    return [(membership, user) for membership, user in rows]
