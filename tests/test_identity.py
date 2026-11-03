from __future__ import annotations

from sqlalchemy import select

from myeconomy.infrastructure.models import (
    AuditEvent,
    AuthSession,
    EmailVerificationChallenge,
    User,
)


def register(client, email="alice@example.com", password="CorrectHorseBattery2026!", name="Alice"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": name},
    )


def test_registration_creates_argon2_account_and_hashed_session(test_environment) -> None:
    client, session_factory = test_environment
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["email_verified"] is False
    assert body["token_type"] == "bearer"

    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "alice@example.com"))
        auth_session = db.scalar(select(AuthSession).where(AuthSession.user_id == user.id))
        assert user is not None
        assert user.password_hash.startswith("$argon2")
        assert "CorrectHorseBattery2026!" not in user.password_hash
        assert auth_session is not None
        assert auth_session.token_hash != body["access_token"]
        assert len(auth_session.token_hash) == 64
        challenge = db.scalar(
            select(EmailVerificationChallenge).where(EmailVerificationChallenge.user_id == user.id)
        )
        assert challenge is not None
        assert challenge.token_hash != client.app.state.verification_tokens[user.email]
        assert len(challenge.token_hash) == 64


def test_email_is_casefolded_and_duplicate_account_is_rejected(test_environment) -> None:
    client, _ = test_environment
    first = register(client, email="Alice@Example.com")
    second = register(client, email="alice@example.com")
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


def test_login_is_case_insensitive_and_bad_credentials_are_generic(test_environment) -> None:
    client, _ = test_environment
    assert register(client).status_code == 201
    good = client.post(
        "/api/v1/auth/login",
        json={"email": "ALICE@example.com", "password": "CorrectHorseBattery2026!"},
    )
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    missing = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
    )
    assert good.status_code == 200
    assert bad.status_code == 401
    assert missing.status_code == 401
    assert bad.json() == missing.json()


def test_protected_route_requires_authentication(test_environment) -> None:
    client, _ = test_environment
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_logout_revokes_session_immediately(test_environment) -> None:
    client, _ = test_environment
    token = register(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_password_policy_rejects_short_or_blank_password(test_environment) -> None:
    client, _ = test_environment
    short = register(client, password="short")
    blankish = register(client, email="blank@example.com", password="            ")
    assert short.status_code == 422
    assert blankish.status_code == 422


def test_authentication_events_are_audited_without_credentials(test_environment) -> None:
    client, session_factory = test_environment
    register(client)
    client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "not-the-password"},
    )
    with session_factory() as db:
        events = list(db.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)))
        actions = [event.action for event in events]
        assert "identity.account_registered" in actions
        assert "identity.session_created" in actions
        assert "identity.login_rejected" in actions
        assert all("password" not in str(event.details).lower() for event in events)


def test_expired_session_is_rejected(test_environment) -> None:
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from myeconomy.infrastructure.models import AuthSession

    client, session_factory = test_environment
    auth_response = register(client)
    with session_factory() as db:
        auth_session = db.scalar(select(AuthSession))
        auth_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_response.json()['access_token']}"},
    )
    assert response.status_code == 401


def test_email_verification_is_required_for_household_and_consent_actions(test_environment) -> None:
    client, _ = test_environment
    response = register(client)
    body = response.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    blocked = client.post("/api/v1/households", headers=headers, json={"name": "Private"})
    assert blocked.status_code == 403
    assert client.get("/api/v1/auth/me", headers=headers).json()["email_verified"] is False

    token = client.app.state.verification_tokens["alice@example.com"]
    verified = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    assert verified.json()["email_verified"] is True
    assert client.get("/api/v1/auth/me", headers=headers).json()["email_verified"] is True

    household = client.post("/api/v1/households", headers=headers, json={"name": "Private"})
    assert household.status_code == 201, household.text
    replay = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert replay.status_code == 400


def test_verification_resend_revokes_old_token_and_enforces_cooldown(test_environment) -> None:
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    client, session_factory = test_environment
    response = register(client)
    body = response.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    old_token = client.app.state.verification_tokens["alice@example.com"]
    rate_limited = client.post("/api/v1/auth/verification/resend", headers=headers)
    assert rate_limited.status_code == 429

    with session_factory() as db:
        challenge = db.scalar(select(EmailVerificationChallenge))
        challenge.created_at = datetime.now(UTC) - timedelta(minutes=2)
        db.commit()

    resent = client.post("/api/v1/auth/verification/resend", headers=headers)
    assert resent.status_code == 202
    new_token = client.app.state.verification_tokens["alice@example.com"]
    assert new_token != old_token
    assert client.post("/api/v1/auth/verify-email", json={"token": old_token}).status_code == 400
    assert client.post("/api/v1/auth/verify-email", json={"token": new_token}).status_code == 200


def test_expired_email_verification_challenge_is_rejected(test_environment) -> None:
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    client, session_factory = test_environment
    response = register(client)
    token = client.app.state.verification_tokens["alice@example.com"]
    with session_factory() as db:
        challenge = db.scalar(select(EmailVerificationChallenge))
        challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    rejected = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert rejected.status_code == 400
    assert (
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {response.json()['access_token']}"},
        ).json()["email_verified"]
        is False
    )
