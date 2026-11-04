import pytest
from sqlalchemy import select

from myeconomy.infrastructure.models import PersonalCase, PersonalCaseEvent


def verified_headers(client, email: str) -> dict[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "CorrectHorseBattery2026!",
            "display_name": "Casebook Test",
        },
    )
    assert registration.status_code == 201, registration.text
    token = registration.json()["access_token"]
    challenge = client.app.state.verification_tokens[email]
    verified = client.post("/api/v1/auth/verify-email", json={"token": challenge})
    assert verified.status_code == 200, verified.text
    return {"Authorization": f"Bearer {token}"}


def create_payload(finding_id: str = "DATA-001") -> dict[str, str | int]:
    return {
        "finding_id": finding_id,
        "period_start": "2026-10-01",
        "period_end": "2026-10-31",
        "as_of": "2026-11-04",
        "currency": "INR",
        "obligation_horizon_days": 30,
    }


def test_case_creation_replays_and_detail_has_immutable_event_timeline(test_environment):
    client, session_factory = test_environment
    headers = verified_headers(client, "casebook-owner@example.com")
    create_headers = {**headers, "Idempotency-Key": "case-open-001"}

    created = client.post(
        "/api/v1/cases/from-finding", json=create_payload(), headers=create_headers
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "OPEN"
    assert body["state_version"] == 1
    assert body["source_snapshot"]["origin"] == "SERVER_COMPUTED_PERSONAL_POWER_REPORT"
    assert body["source_snapshot"]["value_status"] == "NOT_A_VALUE_OUTCOME"
    assert body["replayed"] is False

    replay = client.post(
        "/api/v1/cases/from-finding", json=create_payload(), headers=create_headers
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == body["id"]
    assert replay.json()["replayed"] is True

    detail = client.get(f"/api/v1/cases/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert [event["event_sequence"] for event in detail.json()["events"]] == [1]

    with session_factory() as db:
        case_row = db.scalar(select(PersonalCase))
        case_row.title = "attempted source rewrite"
        try:
            db.flush()
            pytest.fail("case source facts must reject ORM mutations")
        except RuntimeError as exc:
            assert "immutable" in str(exc)
        finally:
            db.rollback()

        event_row = db.scalar(select(PersonalCaseEvent))
        event_row.note = "attempted mutation"
        try:
            db.flush()
            pytest.fail("case events must reject ORM mutations")
        except RuntimeError as exc:
            assert "append-only" in str(exc)
        finally:
            db.rollback()


def test_transition_uses_version_precondition_and_replays_by_key(test_environment):
    client, _ = test_environment
    headers = verified_headers(client, "casebook-transition@example.com")
    created = client.post(
        "/api/v1/cases/from-finding",
        json=create_payload(),
        headers={**headers, "Idempotency-Key": "case-open-002"},
    )
    case_id = created.json()["id"]

    transition_headers = {**headers, "Idempotency-Key": "case-review-001"}
    transition_body = {
        "to_status": "IN_REVIEW",
        "expected_version": 1,
        "note": "I checked the source statement.",
    }
    moved = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json=transition_body,
        headers=transition_headers,
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["status"] == "IN_REVIEW"
    assert moved.json()["state_version"] == 2
    assert [event["event_sequence"] for event in moved.json()["events"]] == [1, 2]

    replay = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json=transition_body,
        headers=transition_headers,
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["state_version"] == 2
    conflicting_replay = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json={"to_status": "CLOSED", "expected_version": 1, "note": "changed request"},
        headers=transition_headers,
    )
    assert conflicting_replay.status_code == 409

    stale = client.post(
        f"/api/v1/cases/{case_id}/transition",
        json={"to_status": "ACTION_READY", "expected_version": 1},
        headers={**headers, "Idempotency-Key": "case-stale-001"},
    )
    assert stale.status_code == 409


def test_case_and_finding_are_owner_scoped_and_client_cannot_inject_facts(test_environment):
    client, _ = test_environment
    owner = verified_headers(client, "casebook-owner-a@example.com")
    stranger = verified_headers(client, "casebook-owner-b@example.com")
    forged_payload = {**create_payload(), "title": "I found fraud", "amount": "999999.00"}
    rejected = client.post(
        "/api/v1/cases/from-finding",
        json=forged_payload,
        headers={**owner, "Idempotency-Key": "case-forged-001"},
    )
    assert rejected.status_code == 422

    created = client.post(
        "/api/v1/cases/from-finding",
        json=create_payload(),
        headers={**owner, "Idempotency-Key": "case-owner-001"},
    )
    case_id = created.json()["id"]
    assert client.get(f"/api/v1/cases/{case_id}", headers=stranger).status_code == 404
    assert client.get("/api/v1/cases", headers=stranger).json() == []


def test_case_creation_idempotency_key_cannot_be_reused_for_another_report(test_environment):
    client, _ = test_environment
    headers = verified_headers(client, "casebook-idempotency@example.com")
    key_headers = {**headers, "Idempotency-Key": "case-idem-001"}
    first = client.post("/api/v1/cases/from-finding", json=create_payload(), headers=key_headers)
    assert first.status_code == 201
    changed = create_payload()
    changed["period_start"] = "2026-09-01"
    changed["period_end"] = "2026-09-30"
    changed["finding_id"] = "DATA-001"
    second = client.post("/api/v1/cases/from-finding", json=changed, headers=key_headers)
    assert second.status_code == 409


def test_case_creation_rejects_unsupported_currency_and_invalid_report_window(test_environment):
    client, _ = test_environment
    headers = verified_headers(client, "casebook-validation@example.com")
    unsupported = create_payload()
    unsupported["currency"] = "ZZZ"
    rejected_currency = client.post(
        "/api/v1/cases/from-finding",
        json=unsupported,
        headers={**headers, "Idempotency-Key": "case-invalid-currency"},
    )
    assert rejected_currency.status_code == 422

    invalid_window = create_payload()
    invalid_window["period_start"] = "2026-11-01"
    invalid_window["period_end"] = "2026-10-31"
    rejected_window = client.post(
        "/api/v1/cases/from-finding",
        json=invalid_window,
        headers={**headers, "Idempotency-Key": "case-invalid-window"},
    )
    assert rejected_window.status_code == 422
