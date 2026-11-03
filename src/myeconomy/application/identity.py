"""Account and opaque-session use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from myeconomy.application.audit import record_audit_event
from myeconomy.domain.errors import (
    AuthenticationError,
    ConflictError,
    RateLimitError,
    VerificationError,
)
from myeconomy.infrastructure.models import AuthSession, EmailVerificationChallenge, User
from myeconomy.infrastructure.security import (
    hash_password,
    hash_session_token,
    issue_session_token,
    password_hash_needs_rehash,
    verify_password,
)

SESSION_TTL = timedelta(hours=12)
EMAIL_VERIFICATION_TTL = timedelta(hours=24)
EMAIL_VERIFICATION_RESEND_COOLDOWN = timedelta(seconds=60)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def _utc(value: datetime) -> datetime:
    # SQLite may return naive datetimes despite timezone=True; interpret stored UTC as UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def register_user(db: Session, *, email: str, password: str, display_name: str) -> User:
    normalized_email = normalize_email(email)
    normalized_name = display_name.strip()
    if not normalized_name:
        raise ValueError("Display name must not be empty.")
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        display_name=normalized_name,
        email_verified=False,
        is_active=True,
    )
    try:
        db.add(user)
        db.flush()
        record_audit_event(
            db,
            actor_user_id=user.id,
            action="identity.account_registered",
            subject_type="user",
            subject_id=str(user.id),
            details={"email_verified": False},
        )
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("An account with this email address already exists.") from exc
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    normalized_email = normalize_email(email)
    user = db.scalar(select(User).where(User.email == normalized_email))
    stored_hash = user.password_hash if user is not None else None
    valid = verify_password(password, stored_hash)
    if user is None or not valid or not user.is_active:
        record_audit_event(
            db,
            actor_user_id=None,
            action="identity.login_rejected",
            subject_type="authentication",
            details={"reason": "invalid_credentials"},
        )
        db.commit()
        raise AuthenticationError("Email or password is incorrect.")

    if password_hash_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    record_audit_event(
        db,
        actor_user_id=user.id,
        action="identity.login_succeeded",
        subject_type="user",
        subject_id=str(user.id),
    )
    db.commit()
    return user


def create_session(db: Session, *, user: User) -> tuple[str, AuthSession]:
    raw_token = issue_session_token()
    now = datetime.now(UTC)
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        created_at=now,
        expires_at=now + SESSION_TTL,
    )
    db.add(auth_session)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=user.id,
        action="identity.session_created",
        subject_type="auth_session",
        subject_id=str(auth_session.id),
    )
    db.commit()
    db.refresh(auth_session)
    return raw_token, auth_session


def resolve_session(db: Session, *, raw_token: str) -> tuple[User, AuthSession]:
    token_hash = hash_session_token(raw_token)
    auth_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))
    now = datetime.now(UTC)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or _utc(auth_session.expires_at) <= now
    ):
        raise AuthenticationError()
    user = db.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError()
    auth_session.last_used_at = now
    db.commit()
    return user, auth_session


def revoke_session(db: Session, *, user: User, auth_session: AuthSession) -> None:
    if auth_session.user_id != user.id:
        raise AuthenticationError()
    if auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.now(UTC)
        record_audit_event(
            db,
            actor_user_id=user.id,
            action="identity.session_revoked",
            subject_type="auth_session",
            subject_id=str(auth_session.id),
        )
        db.commit()


def issue_email_verification_challenge(
    db: Session, *, user: User, enforce_resend_cooldown: bool = False
) -> str:
    """Issue a single-use, expiring email verification token; only its hash is stored."""
    now = datetime.now(UTC)
    existing = db.scalar(
        select(EmailVerificationChallenge)
        .where(
            EmailVerificationChallenge.user_id == user.id,
            EmailVerificationChallenge.consumed_at.is_(None),
            EmailVerificationChallenge.revoked_at.is_(None),
        )
        .order_by(EmailVerificationChallenge.created_at.desc())
        .with_for_update()
    )
    if existing is not None and enforce_resend_cooldown:
        if _utc(existing.created_at) + EMAIL_VERIFICATION_RESEND_COOLDOWN > now:
            raise RateLimitError(
                "A verification message was sent recently. "
                "Wait one minute before requesting another."
            )
    if existing is not None:
        existing.revoked_at = now

    raw_token = issue_session_token()
    challenge = EmailVerificationChallenge(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        created_at=now,
        expires_at=now + EMAIL_VERIFICATION_TTL,
    )
    db.add(challenge)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("A verification challenge could not be created. Retry safely.") from exc
    record_audit_event(
        db,
        actor_user_id=user.id,
        action="identity.email_verification_issued",
        subject_type="email_verification_challenge",
        subject_id=str(challenge.id),
        details={"expires_at": challenge.expires_at.isoformat()},
    )
    db.commit()
    return raw_token


def verify_email_address(db: Session, *, raw_token: str) -> User:
    """Consume a verification token exactly once and mark its account verified."""
    challenge = db.scalar(
        select(EmailVerificationChallenge)
        .where(EmailVerificationChallenge.token_hash == hash_session_token(raw_token))
        .with_for_update()
    )
    now = datetime.now(UTC)
    if (
        challenge is None
        or challenge.consumed_at is not None
        or challenge.revoked_at is not None
        or _utc(challenge.expires_at) <= now
    ):
        raise VerificationError()
    user = db.get(User, challenge.user_id)
    if user is None or not user.is_active:
        raise VerificationError()

    user.email_verified = True
    challenge.consumed_at = now
    pending = db.scalars(
        select(EmailVerificationChallenge).where(
            EmailVerificationChallenge.user_id == user.id,
            EmailVerificationChallenge.id != challenge.id,
            EmailVerificationChallenge.consumed_at.is_(None),
            EmailVerificationChallenge.revoked_at.is_(None),
        )
    ).all()
    for other in pending:
        other.revoked_at = now
    record_audit_event(
        db,
        actor_user_id=user.id,
        action="identity.email_verified",
        subject_type="user",
        subject_id=str(user.id),
        details={"challenge_id": str(challenge.id)},
    )
    db.commit()
    db.refresh(user)
    return user
