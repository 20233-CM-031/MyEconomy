from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from myeconomy.infrastructure.models import AuditEvent, ConsentGrant


def register(client, email: str, name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Long-Unique-Passphrase-2026!",
            "display_name": name,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    verification_token = client.app.state.verification_tokens[email]
    verified = client.post("/api/v1/auth/verify-email", json={"token": verification_token})
    assert verified.status_code == 200, verified.text
    return body


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_consent_is_purpose_and_category_specific_and_revocable(test_environment) -> None:
    client, session_factory = test_environment
    alice = register(client, "alice@example.com", "Alice")
    headers = auth(alice["access_token"])
    created = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "opportunity_matching",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["skills", "availability"],
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
    )
    assert created.status_code == 201, created.text
    grant = created.json()
    assert grant["status"] == "active"

    skills_allowed = client.get(
        "/api/v1/consents/check",
        params={
            "purpose": "opportunity_matching",
            "category": "skills",
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
        headers=headers,
    )
    profile_not_allowed = client.get(
        "/api/v1/consents/check",
        params={
            "purpose": "opportunity_matching",
            "category": "profile",
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
        headers=headers,
    )
    assert skills_allowed.json()["allowed"] is True
    assert profile_not_allowed.json()["allowed"] is False

    revoked = client.post(f"/api/v1/consents/{grant['id']}/revoke", headers=headers)
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    after_revoke = client.get(
        "/api/v1/consents/check",
        params={
            "purpose": "opportunity_matching",
            "category": "skills",
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
        headers=headers,
    )
    assert after_revoke.json()["allowed"] is False

    with session_factory() as db:
        events = list(db.scalars(select(AuditEvent)))
        actions = {event.action for event in events}
        assert "consent.granted" in actions
        assert "consent.revoked" in actions


def test_commons_and_research_cannot_receive_raw_transaction_records(test_environment) -> None:
    client, _ = test_environment
    alice = register(client, "alice@example.com", "Alice")
    headers = auth(alice["access_token"])
    commons = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "commons_aggregation",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["financial_summary", "household_obligations"],
            "recipient_type": "service",
            "recipient_id": "commons",
        },
    )
    assert commons.status_code == 201

    raw_transactions = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "commons_aggregation",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["transaction_records"],
            "recipient_type": "service",
            "recipient_id": "commons",
        },
    )
    research_transactions = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "research_participation",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["transaction_records"],
            "recipient_type": "research",
            "recipient_id": "approved-research-program",
        },
    )
    assert raw_transactions.status_code == 422
    assert research_transactions.status_code == 422


def test_household_consent_requires_membership_and_is_not_implied_by_membership(
    test_environment,
) -> None:
    client, _ = test_environment
    owner = register(client, "owner@example.com", "Owner")
    other = register(client, "other@example.com", "Other")
    household = client.post(
        "/api/v1/households", json={"name": "Family"}, headers=auth(owner["access_token"])
    ).json()

    non_member_grant = client.post(
        "/api/v1/consents",
        headers=auth(other["access_token"]),
        json={
            "purpose": "household_sharing",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["financial_summary"],
            "recipient_type": "household",
            "recipient_id": household["id"],
        },
    )
    assert non_member_grant.status_code == 404

    owner_grant = client.post(
        "/api/v1/consents",
        headers=auth(owner["access_token"]),
        json={
            "purpose": "household_sharing",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["financial_summary"],
            "recipient_type": "household",
            "recipient_id": household["id"],
        },
    )
    assert owner_grant.status_code == 201


def test_expired_consent_is_not_authorized(test_environment) -> None:
    client, session_factory = test_environment
    alice = register(client, "alice@example.com", "Alice")
    created = client.post(
        "/api/v1/consents",
        headers=auth(alice["access_token"]),
        json={
            "purpose": "opportunity_matching",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["skills"],
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
    )
    assert created.status_code == 201
    with session_factory() as db:
        grant = db.get(ConsentGrant, UUID(created.json()["id"]))
        from datetime import UTC, datetime, timedelta

        grant.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    result = client.get(
        "/api/v1/consents/check",
        params={
            "purpose": "opportunity_matching",
            "category": "skills",
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
        headers=auth(alice["access_token"]),
    )
    assert result.status_code == 200
    assert result.json()["allowed"] is False


def test_user_cannot_revoke_another_users_consent(test_environment) -> None:
    client, _ = test_environment
    alice = register(client, "alice@example.com", "Alice")
    bob = register(client, "bob@example.com", "Bob")
    consent = client.post(
        "/api/v1/consents",
        headers=auth(alice["access_token"]),
        json={
            "purpose": "opportunity_matching",
            "terms_version": "2026-11-03.1",
            "confirmed": True,
            "data_categories": ["skills"],
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
        },
    ).json()
    response = client.post(
        f"/api/v1/consents/{consent['id']}/revoke", headers=auth(bob["access_token"])
    )
    assert response.status_code == 404


def test_audit_table_rejects_direct_sql_mutation(test_environment) -> None:
    client, session_factory = test_environment
    register(client, "alice@example.com", "Alice")
    with session_factory() as db:
        event = db.scalar(select(AuditEvent).limit(1))
        try:
            db.execute(
                update(AuditEvent).where(AuditEvent.id == event.id).values(action="tampered")
            )
            db.commit()
            raise AssertionError("Audit mutation unexpectedly succeeded")
        except IntegrityError:
            db.rollback()


def test_terms_are_discoverable_and_outdated_terms_are_rejected(test_environment) -> None:
    client, _ = test_environment
    terms_response = client.get("/api/v1/consents/terms")
    assert terms_response.status_code == 200
    terms = {item["purpose"]: item for item in terms_response.json()}
    commons_terms = terms["commons_aggregation"]
    assert commons_terms["version"] == "2026-11-03.1"
    assert "transaction_records" not in commons_terms["allowed_categories"]
    note = commons_terms["revocation_note"].lower()
    assert "revocation" in note

    alice = register(client, "terms@example.com", "Terms User")
    outdated = client.post(
        "/api/v1/consents",
        headers=auth(alice["access_token"]),
        json={
            "purpose": "commons_aggregation",
            "data_categories": ["financial_summary"],
            "recipient_type": "service",
            "recipient_id": "commons",
            "terms_version": "v0-old",
            "confirmed": True,
        },
    )
    assert outdated.status_code == 422


def test_consent_requires_explicit_confirmation_flag(test_environment) -> None:
    client, _ = test_environment
    alice = register(client, "confirm@example.com", "Confirm User")
    response = client.post(
        "/api/v1/consents",
        headers=auth(alice["access_token"]),
        json={
            "purpose": "opportunity_matching",
            "data_categories": ["skills"],
            "recipient_type": "service",
            "recipient_id": "opportunity-engine",
            "terms_version": "2026-11-03.1",
        },
    )
    assert response.status_code == 422
