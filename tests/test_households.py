from __future__ import annotations


def register(client, email: str, display_name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Long-Unique-Passphrase-2026!",
            "display_name": display_name,
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


def test_invitation_requires_acceptance_by_the_invited_email(test_environment) -> None:
    client, _ = test_environment
    owner = register(client, "owner@example.com", "Owner")
    invitee = register(client, "invitee@example.com", "Invitee")
    wrong_person = register(client, "other@example.com", "Other")

    household = client.post(
        "/api/v1/households", json={"name": "Family"}, headers=auth(owner["access_token"])
    ).json()
    invitation_response = client.post(
        f"/api/v1/households/{household['id']}/invitations",
        json={"email": "invitee@example.com"},
        headers=auth(owner["access_token"]),
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.json()
    assert invitation["delivery_status"] == "manual_share_required"

    # Membership metadata is not visible to a non-member.
    denied = client.get(
        f"/api/v1/households/{household['id']}/members",
        headers=auth(invitee["access_token"]),
    )
    assert denied.status_code == 404

    wrong_accept = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": invitation["invitation_token"]},
        headers=auth(wrong_person["access_token"]),
    )
    assert wrong_accept.status_code == 401

    accepted = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": invitation["invitation_token"]},
        headers=auth(invitee["access_token"]),
    )
    assert accepted.status_code == 200
    assert accepted.json()["role"] == "member"
    members = client.get(
        f"/api/v1/households/{household['id']}/members",
        headers=auth(invitee["access_token"]),
    )
    assert members.status_code == 200
    assert len(members.json()) == 2
    assert all("email" not in member for member in members.json())

    # Joining a household does not silently grant access to personal/financial data.
    consents = client.get("/api/v1/consents", headers=auth(invitee["access_token"]))
    assert consents.status_code == 200
    assert consents.json() == []

    replay = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": invitation["invitation_token"]},
        headers=auth(invitee["access_token"]),
    )
    assert replay.status_code == 409


def test_only_household_owner_can_issue_invitation(test_environment) -> None:
    client, _ = test_environment
    owner = register(client, "owner@example.com", "Owner")
    member = register(client, "member@example.com", "Member")
    register(client, "target@example.com", "Target")

    household = client.post(
        "/api/v1/households", json={"name": "Household"}, headers=auth(owner["access_token"])
    ).json()
    invite = client.post(
        f"/api/v1/households/{household['id']}/invitations",
        json={"email": "member@example.com"},
        headers=auth(owner["access_token"]),
    ).json()
    accepted = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": invite["invitation_token"]},
        headers=auth(member["access_token"]),
    )
    assert accepted.status_code == 200

    forbidden = client.post(
        f"/api/v1/households/{household['id']}/invitations",
        json={"email": "target@example.com"},
        headers=auth(member["access_token"]),
    )
    assert forbidden.status_code == 403


def test_duplicate_active_invitation_is_rejected(test_environment) -> None:
    client, _ = test_environment
    owner = register(client, "owner@example.com", "Owner")
    household = client.post(
        "/api/v1/households", json={"name": "Family"}, headers=auth(owner["access_token"])
    ).json()
    path = f"/api/v1/households/{household['id']}/invitations"
    headers = auth(owner["access_token"])
    first = client.post(path, json={"email": "new@example.com"}, headers=headers)
    second = client.post(path, json={"email": "NEW@example.com"}, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 409


def test_invitation_revocation_prevents_acceptance(test_environment) -> None:
    client, _ = test_environment
    owner = register(client, "owner@example.com", "Owner")
    invitee = register(client, "invitee@example.com", "Invitee")
    household = client.post(
        "/api/v1/households", json={"name": "Family"}, headers=auth(owner["access_token"])
    ).json()
    invitation = client.post(
        f"/api/v1/households/{household['id']}/invitations",
        json={"email": "invitee@example.com"},
        headers=auth(owner["access_token"]),
    ).json()
    revoked = client.post(
        f"/api/v1/household-invitations/{invitation['id']}/revoke",
        headers=auth(owner["access_token"]),
    )
    accepted = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": invitation["invitation_token"]},
        headers=auth(invitee["access_token"]),
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert accepted.status_code == 409


def test_expired_invitation_cannot_be_accepted_and_can_be_reissued(test_environment) -> None:
    from datetime import UTC, datetime, timedelta
    from uuid import UUID

    from sqlalchemy import select

    from myeconomy.infrastructure.models import HouseholdInvitation

    client, session_factory = test_environment
    owner = register(client, "owner@example.com", "Owner")
    invitee = register(client, "invitee@example.com", "Invitee")
    household = client.post(
        "/api/v1/households", json={"name": "Family"}, headers=auth(owner["access_token"])
    ).json()
    path = f"/api/v1/households/{household['id']}/invitations"
    first = client.post(
        path, json={"email": "invitee@example.com"}, headers=auth(owner["access_token"])
    )
    with session_factory() as db:
        stored = db.scalar(
            select(HouseholdInvitation).where(HouseholdInvitation.id == UUID(first.json()["id"]))
        )
        assert stored.token_hash != first.json()["invitation_token"]
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    rejected = client.post(
        "/api/v1/household-invitations/accept",
        json={"invitation_token": first.json()["invitation_token"]},
        headers=auth(invitee["access_token"]),
    )
    assert rejected.status_code == 409

    second = client.post(
        path, json={"email": "invitee@example.com"}, headers=auth(owner["access_token"])
    )
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
