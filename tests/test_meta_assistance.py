from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest

from myeconomy.application.meta_assistance import build_meta_safe_summary
from myeconomy.domain.consent import (
    ConsentPurpose,
    DataCategory,
    RecipientType,
    validate_consent_scope,
)
from myeconomy.domain.errors import ConsentScopeError
from myeconomy.domain.personal_power import (
    PersonalPowerInput,
    UpcomingObligation,
    build_personal_power_report,
)
from myeconomy.infrastructure.meta_model_api import (
    META_MODEL_ID,
    MetaModelUnavailable,
    call_personal_explanation,
)


def _report():
    return build_personal_power_report(
        PersonalPowerInput(
            owner_reference="owner-secret-not-exported",
            currency="INR",
            period_start=date(2026, 10, 1),
            period_end=date(2026, 10, 31),
            as_of=date(2026, 11, 4),
            account_count=1,
            posted_transaction_count=4,
            income_total=Decimal("50000.00"),
            gross_expenses=Decimal("61000.00"),
            refunds=Decimal("0.00"),
            essential_expenses=Decimal("45000.00"),
            discretionary_expenses=Decimal("16000.00"),
            net_cashflow=Decimal("-11000.00"),
        )
    )


def test_ai_assistance_consent_is_only_for_financial_summary_and_exact_service():
    validate_consent_scope(
        purpose=ConsentPurpose.AI_ASSISTANCE,
        categories=[DataCategory.FINANCIAL_SUMMARY, DataCategory.HOUSEHOLD_OBLIGATIONS],
        recipient_type=RecipientType.SERVICE,
        recipient_id="meta-model-api",
    )
    with pytest.raises(ConsentScopeError):
        validate_consent_scope(
            purpose=ConsentPurpose.AI_ASSISTANCE,
            categories=[DataCategory.TRANSACTION_RECORDS],
            recipient_type=RecipientType.SERVICE,
            recipient_id="meta-model-api",
        )
    with pytest.raises(ConsentScopeError):
        validate_consent_scope(
            purpose=ConsentPurpose.AI_ASSISTANCE,
            categories=[DataCategory.FINANCIAL_SUMMARY],
            recipient_type=RecipientType.SERVICE,
            recipient_id="other-provider",
        )


def test_summary_excludes_owner_ids_transaction_references_and_user_payee_labels():
    report = build_personal_power_report(
        PersonalPowerInput(
            owner_reference="owner-secret-not-exported",
            currency="INR",
            period_start=date(2026, 10, 1),
            period_end=date(2026, 10, 31),
            as_of=date(2026, 11, 4),
            account_count=1,
            posted_transaction_count=4,
            income_total=Decimal("50000.00"),
            gross_expenses=Decimal("61000.00"),
            refunds=Decimal("0.00"),
            essential_expenses=Decimal("45000.00"),
            discretionary_expenses=Decimal("16000.00"),
            net_cashflow=Decimal("-11000.00"),
            upcoming_obligations=(
                UpcomingObligation(
                    obligation_id="obl-1",
                    payee_label="SECRET-PAYEE-ALPHA",
                    amount=Decimal("1800.00"),
                    currency="INR",
                    next_due_date=date(2026, 11, 7),
                    frequency="MONTHLY",
                    essential=True,
                ),
            ),
        )
    )
    summary, finding_ids = build_meta_safe_summary(
        report,
        question="What should I review first?",
    )
    serialized = json.dumps(summary)
    assert "owner-secret-not-exported" not in serialized
    assert "transaction_id" not in serialized
    assert "source_references" not in serialized
    assert "SECRET-PAYEE-ALPHA" not in serialized
    assert set(finding_ids) == {item.finding_id for item in report.findings}
    assert summary["data_scope"] == "AGGREGATE_FINANCIAL_SUMMARY_AND_HOUSEHOLD_OBLIGATIONS"


def test_gateway_uses_standard_model_and_schema_constrained_completion(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "summary": "Review the unusually high essential outflow.",
                                        "actions": [
                                            {
                                                "finding_id": "CASH-001",
                                                "why_it_matters": (
                                                    "Classified outflow exceeded inflow."
                                                ),
                                                "next_step": (
                                                    "Compare the largest essential bills with "
                                                    "their source documents."
                                                ),
                                                "uncertainty": (
                                                    "Only imported posted records are represented."
                                                ),
                                            }
                                        ],
                                        "limitations": [
                                            "This explanation does not prove a saving or recovery."
                                        ],
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode()

    def fake_opener(request, timeout):
        captured["request"] = json.loads(request.data.decode())
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return FakeResponse()

    result = call_personal_explanation(
        question="What first?",
        personal_summary={"aggregates": {"net_cashflow": "-1000.00"}},
        allowed_finding_ids={"CASH-001"},
        api_key="test-key",
        opener=fake_opener,
    )
    assert result["model"] == META_MODEL_ID == "muse-spark-1.3"
    assert result["mode"] == "STANDARD"
    assert captured["request"]["store"] is False
    assert "tools" not in captured["request"]
    assert captured["request"]["response_format"]["type"] == "json_schema"
    assert "contributor" not in captured["request"]["model"]


def test_gateway_rejects_unknown_finding_reference():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "summary": "Summary.",
                                        "actions": [
                                            {
                                                "finding_id": "UNKNOWN",
                                                "why_it_matters": "Why.",
                                                "next_step": "Check it.",
                                                "uncertainty": "Unknown.",
                                            }
                                        ],
                                        "limitations": ["Not a verified outcome."],
                                    }
                                )
                            }
                        }
                    ]
                }
            ).encode()

    with pytest.raises(MetaModelUnavailable):
        call_personal_explanation(
            question="Explain",
            personal_summary={},
            allowed_finding_ids={"KNOWN"},
            api_key="test-key",
            opener=lambda *_args, **_kwargs: FakeResponse(),
        )


def test_gateway_fails_closed_without_api_key(monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(MetaModelUnavailable):
        call_personal_explanation(
            question="Explain",
            personal_summary={},
            allowed_finding_ids=set(),
            api_key=None,
        )
