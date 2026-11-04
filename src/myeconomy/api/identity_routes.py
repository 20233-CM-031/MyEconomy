"""Identity, household and consent HTTP endpoints."""

from __future__ import annotations

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from myeconomy.api.dependencies import (
    AuthContext,
    require_authentication,
    require_verified_authentication,
)
from myeconomy.api.identity_schemas import (
    AuthResponse,
    ConsentCheckResponse,
    ConsentGrantRequest,
    ConsentGrantResponse,
    ConsentTermsResponse,
    EmailVerificationResponse,
    HouseholdCreateRequest,
    HouseholdInvitationAcceptRequest,
    HouseholdInvitationCreateRequest,
    HouseholdInvitationResponse,
    HouseholdInvitationRevokedResponse,
    HouseholdMemberResponse,
    HouseholdResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)
from myeconomy.application.consents import (
    create_consent,
    effective_status,
    has_active_consent,
    list_consents,
    revoke_consent,
)
from myeconomy.application.households import (
    accept_household_invitation,
    create_household,
    create_household_invitation,
    list_household_members,
    list_households,
    revoke_household_invitation,
)
from myeconomy.application.identity import (
    authenticate_user,
    create_session,
    issue_email_verification_challenge,
    register_user,
    revoke_session,
    verify_email_address,
)
from myeconomy.domain.consent import (
    ConsentPurpose,
    DataCategory,
    RecipientType,
    allowed_categories_for_purpose,
    list_consent_terms,
    required_recipient_type,
)
from myeconomy.domain.errors import ServiceUnavailableError
from myeconomy.infrastructure.database import get_db
from myeconomy.infrastructure.email_delivery import (
    EmailDeliveryFailure,
    send_verification_email,
)
from myeconomy.infrastructure.models import Household, User

router = APIRouter(prefix="/api/v1", tags=["identity-and-trust"])


def _utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        email_verified=user.email_verified,
        created_at=_utc(user.created_at),
    )


def _auth_response(raw_token: str, session, user: User) -> AuthResponse:
    return AuthResponse(
        access_token=raw_token,
        expires_at=_utc(session.expires_at),
        user=_user_response(user),
    )


def _consent_response(grant) -> ConsentGrantResponse:
    return ConsentGrantResponse(
        id=grant.id,
        purpose=grant.purpose,
        data_categories=grant.data_categories,
        recipient_type=grant.recipient_type,
        recipient_id=grant.recipient_id,
        terms_version=grant.terms_version,
        status=effective_status(grant),
        granted_at=_utc(grant.granted_at),
        expires_at=_utc(grant.expires_at),
        revoked_at=_utc(grant.revoked_at) if grant.revoked_at else None,
    )


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and establish a private session",
)
def register_endpoint(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = register_user(
        db,
        email=str(payload.email),
        password=payload.password.get_secret_value(),
        display_name=payload.display_name,
    )
    token, auth_session = create_session(db, user=user)
    verification_token = issue_email_verification_challenge(db, user=user)
    try:
        send_verification_email(recipient=user.email, token=verification_token)
    except EmailDeliveryFailure as exc:
        raise ServiceUnavailableError(
            "Account created, but verification delivery failed. Sign in and request a resend."
        ) from exc
    return _auth_response(token, auth_session, user)


@router.post(
    "/auth/verify-email",
    response_model=EmailVerificationResponse,
    summary="Verify account email using a single-use challenge",
)
def verify_email_endpoint(
    payload: VerifyEmailRequest, db: Session = Depends(get_db)
) -> EmailVerificationResponse:
    verify_email_address(db, raw_token=payload.token)
    return EmailVerificationResponse(email_verified=True)


@router.post(
    "/auth/verification/resend",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Resend email verification to the authenticated account",
)
def resend_verification_endpoint(
    auth: AuthContext = Depends(require_authentication),
    db: Session = Depends(get_db),
) -> Response:
    if auth.user.email_verified:
        return Response(status_code=status.HTTP_202_ACCEPTED)
    verification_token = issue_email_verification_challenge(
        db, user=auth.user, enforce_resend_cooldown=True
    )
    try:
        send_verification_email(recipient=auth.user.email, token=verification_token)
    except EmailDeliveryFailure as exc:
        raise ServiceUnavailableError("Verification delivery failed. Retry later.") from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/auth/login", response_model=AuthResponse, summary="Create an authenticated session")
def login_endpoint(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(
        db,
        email=str(payload.email),
        password=payload.password.get_secret_value(),
    )
    token, auth_session = create_session(db, user=user)
    return _auth_response(token, auth_session, user)


@router.post(
    "/auth/demo-session",
    response_model=AuthResponse,
    summary="Instant 1-click test demo session",
)
def demo_session_endpoint(db: Session = Depends(get_db)) -> AuthResponse:
    from sqlalchemy import select

    demo_email = "demo@example.com"
    stmt = select(User).where(User.email == demo_email)
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        user = register_user(
            db,
            email=demo_email,
            password="Password12345!",
            display_name="AwnNORA Demo Explorer",
        )
        user.email_verified = True
        db.commit()
        db.refresh(user)
    elif not user.email_verified:
        user.email_verified = True
        db.commit()
        db.refresh(user)
    token, auth_session = create_session(db, user=user)
    return _auth_response(token, auth_session, user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(
    auth: AuthContext = Depends(require_authentication),
    db: Session = Depends(get_db),
) -> Response:
    revoke_session(db, user=auth.user, auth_session=auth.session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/me", response_model=UserResponse, summary="Read the current account")
def me_endpoint(auth: AuthContext = Depends(require_authentication)) -> UserResponse:
    return _user_response(auth.user)


@router.post(
    "/households",
    response_model=HouseholdResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_household_endpoint(
    payload: HouseholdCreateRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> HouseholdResponse:
    household = create_household(db, owner=auth.user, name=payload.name)
    return HouseholdResponse(
        id=household.id,
        name=household.name,
        role="owner",
        created_at=_utc(household.created_at),
    )


@router.get("/households", response_model=list[HouseholdResponse])
def list_households_endpoint(
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[HouseholdResponse]:
    return [
        HouseholdResponse(
            id=household.id,
            name=household.name,
            role=role,
            created_at=_utc(household.created_at),
        )
        for household, role in list_households(db, user_id=auth.user.id)
    ]


@router.post(
    "/households/{household_id}/invitations",
    response_model=HouseholdInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_household_invitation_endpoint(
    household_id: UUID,
    payload: HouseholdInvitationCreateRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> HouseholdInvitationResponse:
    invitation, raw_token = create_household_invitation(
        db,
        actor=auth.user,
        household_id=household_id,
        invited_email=str(payload.email),
    )
    return HouseholdInvitationResponse(
        id=invitation.id,
        household_id=invitation.household_id,
        invited_email=invitation.invited_email,
        invitation_token=raw_token,
        expires_at=_utc(invitation.expires_at),
    )


@router.post("/household-invitations/accept", response_model=HouseholdResponse)
def accept_household_invitation_endpoint(
    payload: HouseholdInvitationAcceptRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> HouseholdResponse:
    membership = accept_household_invitation(
        db, actor=auth.user, raw_token=payload.invitation_token
    )
    household = db.get(Household, membership.household_id)
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")
    return HouseholdResponse(
        id=household.id,
        name=household.name,
        role=membership.role,
        created_at=_utc(household.created_at),
    )


@router.post(
    "/household-invitations/{invitation_id}/revoke",
    response_model=HouseholdInvitationRevokedResponse,
)
def revoke_household_invitation_endpoint(
    invitation_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> HouseholdInvitationRevokedResponse:
    invitation = revoke_household_invitation(db, actor=auth.user, invitation_id=invitation_id)
    return HouseholdInvitationRevokedResponse(
        id=invitation.id,
        status="revoked" if invitation.revoked_at else "active",
        revoked_at=_utc(invitation.revoked_at) if invitation.revoked_at else None,
    )


@router.get(
    "/households/{household_id}/members",
    response_model=list[HouseholdMemberResponse],
)
def list_household_members_endpoint(
    household_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[HouseholdMemberResponse]:
    return [
        HouseholdMemberResponse(
            user_id=member.id,
            display_name=member.display_name,
            role=membership.role,
            joined_at=_utc(membership.created_at),
        )
        for membership, member in list_household_members(
            db, actor=auth.user, household_id=household_id
        )
    ]


@router.get("/consents/terms", response_model=list[ConsentTermsResponse])
def consent_terms_endpoint() -> list[ConsentTermsResponse]:
    """Return the current versioned consent text so clients can render it before opt-in."""
    terms = list_consent_terms()
    return [
        ConsentTermsResponse(
            purpose=item.purpose,
            version=item.version,
            title=item.title,
            summary=item.summary,
            allowed_categories=sorted(
                allowed_categories_for_purpose(item.purpose), key=lambda category: category.value
            ),
            recipient_type=required_recipient_type(item.purpose),
            revocation_note=item.revocation_note,
        )
        for item in terms
    ]


@router.post(
    "/consents",
    response_model=ConsentGrantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant scoped, time-bounded consent for a specific purpose",
)
def create_consent_endpoint(
    payload: ConsentGrantRequest,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> ConsentGrantResponse:
    grant = create_consent(
        db,
        subject=auth.user,
        purpose=payload.purpose,
        categories=payload.data_categories,
        recipient_type=payload.recipient_type,
        recipient_id=payload.recipient_id,
        terms_version=payload.terms_version,
        expires_at=payload.expires_at,
    )
    return _consent_response(grant)


@router.get("/consents", response_model=list[ConsentGrantResponse])
def list_consents_endpoint(
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> list[ConsentGrantResponse]:
    return [_consent_response(grant) for grant in list_consents(db, subject_user_id=auth.user.id)]


@router.post("/consents/{consent_id}/revoke", response_model=ConsentGrantResponse)
def revoke_consent_endpoint(
    consent_id: UUID,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> ConsentGrantResponse:
    grant = revoke_consent(db, subject=auth.user, consent_id=consent_id)
    return _consent_response(grant)


@router.get("/consents/check", response_model=ConsentCheckResponse)
def check_consent_endpoint(
    purpose: ConsentPurpose,
    category: DataCategory,
    recipient_type: RecipientType,
    recipient_id: str,
    auth: AuthContext = Depends(require_verified_authentication),
    db: Session = Depends(get_db),
) -> ConsentCheckResponse:
    allowed = has_active_consent(
        db,
        subject_user_id=auth.user.id,
        purpose=purpose,
        category=category,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
    )
    return ConsentCheckResponse(
        allowed=allowed,
        purpose=purpose,
        category=category,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
    )
