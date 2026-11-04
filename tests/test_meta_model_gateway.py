from __future__ import annotations

import json

import pytest

from myeconomy.infrastructure.meta_model_api import MetaModelUnavailable, call_personal_explanation


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.body[:limit]


def _provider_body(finding_id: str = "CASH-001") -> bytes:
    completion = {
        "summary": "Classified expenses exceed classified income in this period.",
        "actions": [
            {
                "finding_id": finding_id,
                "why_it_matters": "The selected period is in deficit.",
                "next_step": "Check the source records and essential due dates.",
                "uncertainty": "The report only covers imported, classified records.",
            }
        ],
        "limitations": ["This is an explanation, not an external action."],
    }
    return json.dumps({"choices": [{"message": {"content": json.dumps(completion)}}]}).encode()


def test_gateway_pins_standard_model_disables_storage_and_tools() -> None:
    observed: dict[str, object] = {}

    def opener(request, timeout):
        observed["url"] = request.full_url
        observed["headers"] = dict(request.header_items())
        observed["body"] = json.loads(request.data.decode())
        observed["timeout"] = timeout
        return FakeResponse(_provider_body())

    result = call_personal_explanation(
        question="Prioritize the findings.",
        personal_summary={"aggregates": {"net_cashflow": "-100.00"}},
        allowed_finding_ids={"CASH-001"},
        api_key="test-only-key",
        opener=opener,
    )

    body = observed["body"]
    assert observed["url"] == "https://api.meta.ai/v1/chat/completions"
    assert body["model"] == "muse-spark-1.3"
    assert body["store"] is False
    assert body["reasoning_effort"] == "medium"
    assert "tools" not in body
    assert body["response_format"]["type"] == "json_schema"
    assert "test-only-key" not in json.dumps(body)
    assert result["model"] == "muse-spark-1.3"
    assert result["mode"] == "STANDARD"
    assert result["external_actions_taken"] is False


def test_gateway_rejects_unknown_finding_references() -> None:
    with pytest.raises(MetaModelUnavailable, match="unknown finding"):
        call_personal_explanation(
            question="Prioritize the findings.",
            personal_summary={"aggregates": {}},
            allowed_finding_ids={"CASH-001"},
            api_key="test-only-key",
            opener=lambda *_args, **_kwargs: FakeResponse(_provider_body("PRIVATE-999")),
        )


def test_gateway_rejects_unverified_outcome_claims_and_currency_amounts() -> None:
    for unsafe_summary in (
        "Your refund has been paid.",
        "The total is ₹1,250.00.",
    ):
        completion = {
            "summary": unsafe_summary,
            "actions": [],
            "limitations": ["Review required."],
        }
        body = json.dumps({"choices": [{"message": {"content": json.dumps(completion)}}]}).encode()
        with pytest.raises(MetaModelUnavailable):
            call_personal_explanation(
                question="Explain the report.",
                personal_summary={"aggregates": {}},
                allowed_finding_ids=set(),
                api_key="test-only-key",
                opener=lambda *_args, b=body, **_kwargs: FakeResponse(b),
            )


def test_gateway_fails_closed_without_server_key() -> None:
    with pytest.raises(MetaModelUnavailable, match="MODEL_API_KEY"):
        call_personal_explanation(
            question="Explain the report.",
            personal_summary={},
            allowed_finding_ids=set(),
            api_key="",
            opener=lambda *_args, **_kwargs: FakeResponse(b"{}"),
        )
