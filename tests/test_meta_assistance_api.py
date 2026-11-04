from __future__ import annotations

from sqlalchemy import select

from myeconomy.infrastructure.models import AuditEvent


def _verified_user(client, email="meta-demo@example.com"):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "A-Long-Unique-Passphrase-2026!",
            "display_name": "Meta Demo",
        },
    )
    assert registered.status_code == 201, registered.text
    token = client.app.state.verification_tokens[email]
    assert client.post("/api/v1/auth/verify-email", json={"token": token}).status_code == 200
    return registered.json()["access_token"]


def test_meta_explanation_requires_separate_ai_assistance_consent(test_environment):
    client, _ = test_environment
    token = _verified_user(client)
    response = client.post(
        "/api/v1/intelligence/personal-explanation",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "period_start": "2026-10-01",
            "period_end": "2026-10-31",
            "as_of": "2026-11-04",
            "currency": "INR",
            "question_intent": "prioritize_findings",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "consent_required"


def test_meta_explanation_uses_consent_and_returns_non_mutating_result(
    test_environment, monkeypatch
):
    client, session_factory = test_environment
    token = _verified_user(client, "meta-enabled@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    terms = client.get("/api/v1/consents/terms", headers=headers)
    assert terms.status_code == 200
    ai_terms = next(item for item in terms.json() if item["purpose"] == "ai_assistance")
    partial_grant = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "ai_assistance",
            "data_categories": ["financial_summary"],
            "recipient_type": "service",
            "recipient_id": "meta-model-api",
            "terms_version": ai_terms["version"],
            "confirmed": True,
        },
    )
    assert partial_grant.status_code == 201, partial_grant.text
    payload = {
        "period_start": "2026-10-01",
        "period_end": "2026-10-31",
        "as_of": "2026-11-04",
        "currency": "INR",
        "question_intent": "prioritize_findings",
    }
    blocked_without_obligation_scope = client.post(
        "/api/v1/intelligence/personal-explanation", headers=headers, json=payload
    )
    assert blocked_without_obligation_scope.status_code == 403

    grant = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "purpose": "ai_assistance",
            "data_categories": ["financial_summary", "household_obligations"],
            "recipient_type": "service",
            "recipient_id": "meta-model-api",
            "terms_version": ai_terms["version"],
            "confirmed": True,
        },
    )
    assert grant.status_code == 201, grant.text

    def fake_call(*, question, personal_summary, allowed_finding_ids):
        assert (
            question
            == "Prioritize the report findings and suggest the safest first evidence check."
        )
        assert (
            personal_summary["data_scope"]
            == "AGGREGATE_FINANCIAL_SUMMARY_AND_HOUSEHOLD_OBLIGATIONS"
        )
        assert "transaction_rows_or_identifiers" in personal_summary["not_included"]
        assert "DATA-001" in allowed_finding_ids
        return {
            "summary": "Your selected period has no posted records to analyze yet.",
            "actions": [
                {
                    "finding_id": "DATA-001",
                    "why_it_matters": (
                        "There is not enough imported data for a reliable cashflow picture."
                    ),
                    "next_step": "Import one statement and review its transaction classifications.",
                    "uncertainty": "This says nothing about income held outside this account.",
                }
            ],
            "limitations": ["No external provider was contacted."],
            "model": "muse-spark-1.3",
            "mode": "STANDARD",
        }

    monkeypatch.setattr("myeconomy.api.meta_assistance_routes.call_personal_explanation", fake_call)
    response = client.post(
        "/api/v1/intelligence/personal-explanation",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.json()["model"] == "muse-spark-1.3"
    assert response.json()["mode"] == "STANDARD"
    assert response.json()["external_actions_taken"] is False
    assert response.json()["actions"][0]["finding_id"] == "DATA-001"

    with session_factory() as db:
        actions = set(db.scalars(select(AuditEvent.action)).all())
        assert "intelligence.meta_explanation.requested" in actions
        assert "intelligence.meta_explanation.completed" in actions
