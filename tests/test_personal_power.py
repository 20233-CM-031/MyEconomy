from datetime import date
from decimal import Decimal

import pytest

from myeconomy.domain.personal_power import (
    DuplicateCandidate,
    PersonalPowerInput,
    PersonalPowerRuleError,
    UpcomingObligation,
    build_personal_power_report,
)


def base_input(**overrides):
    values = {
        "owner_reference": "owner-demo-1",
        "currency": "INR",
        "period_start": date(2026, 10, 1),
        "period_end": date(2026, 10, 31),
        "as_of": date(2026, 11, 1),
        "account_count": 1,
        "posted_transaction_count": 10,
        "income_total": Decimal("50000.00"),
        "gross_expenses": Decimal("42000.00"),
        "refunds": Decimal("1000.00"),
        "essential_expenses": Decimal("30000.00"),
        "discretionary_expenses": Decimal("12000.00"),
        "net_cashflow": Decimal("9000.00"),
    }
    values.update(overrides)
    return PersonalPowerInput(**values)


def test_negative_cashflow_is_flagged_without_loan_push():
    report = build_personal_power_report(
        base_input(
            income_total=Decimal("20000.00"),
            gross_expenses=Decimal("25000.00"),
            refunds=Decimal("0.00"),
            essential_expenses=Decimal("18000.00"),
            discretionary_expenses=Decimal("7000.00"),
            net_cashflow=Decimal("-5000.00"),
        )
    )
    finding = next(x for x in report.findings if x.code == "NEGATIVE_NET_CASHFLOW")
    assert finding.priority == "HIGH"
    assert "loan" in finding.recommended_next_step.lower()
    assert report.verified_value_created == Decimal("0")
    assert report.read_only is True
    assert report.external_actions_taken is False


def test_duplicate_candidate_is_a_review_signal_not_recovered_value():
    candidate = DuplicateCandidate(
        transaction_id="tx-2",
        amount=Decimal("499.00"),
        currency="INR",
        occurred_on=date(2026, 10, 15),
        possible_duplicate_of_id="tx-1",
        description="Synthetic duplicate candidate",
    )
    report = build_personal_power_report(base_input(duplicate_candidates=(candidate,)))
    finding = next(x for x in report.findings if x.code == "POSSIBLE_DUPLICATE_TRANSACTION")
    assert finding.amount == Decimal("499.00")
    assert finding.source_references == ("tx-2", "tx-1")
    assert finding.value_status == "NOT_A_VALUE_OUTCOME"
    assert report.verified_value_created == Decimal("0")


def test_overdue_and_near_term_essential_obligations_are_visible():
    obligations = (
        UpcomingObligation(
            "obl-1",
            "Synthetic electricity",
            Decimal("1800.00"),
            "INR",
            date(2026, 10, 30),
            "MONTHLY",
            True,
        ),
        UpcomingObligation(
            "obl-2",
            "Synthetic broadband",
            Decimal("900.00"),
            "INR",
            date(2026, 11, 5),
            "MONTHLY",
            True,
        ),
        UpcomingObligation(
            "obl-3",
            "Optional streaming",
            Decimal("299.00"),
            "INR",
            date(2026, 11, 7),
            "MONTHLY",
            False,
        ),
    )
    report = build_personal_power_report(base_input(upcoming_obligations=obligations))
    assert report.upcoming_obligation_count == 3
    assert report.upcoming_essential_obligations == Decimal("2700.00")
    assert any("overdue" in f.title for f in report.findings)


def test_empty_period_does_not_invent_income_or_opportunities():
    report = build_personal_power_report(
        base_input(
            posted_transaction_count=0,
            income_total=Decimal("0.00"),
            gross_expenses=Decimal("0.00"),
            refunds=Decimal("0.00"),
            essential_expenses=Decimal("0.00"),
            discretionary_expenses=Decimal("0.00"),
            net_cashflow=Decimal("0.00"),
        )
    )
    assert report.findings[0].code == "NO_POSTED_DATA"
    assert report.verified_value_created == Decimal("0")


def test_rejects_inconsistent_arithmetic_and_mixed_currency():
    with pytest.raises(PersonalPowerRuleError):
        base_input(net_cashflow=Decimal("123.00"))
    candidate = DuplicateCandidate(
        "tx-1", Decimal("5.00"), "USD", date(2026, 10, 1), "tx-0", "test"
    )
    with pytest.raises(PersonalPowerRuleError):
        base_input(duplicate_candidates=(candidate,))


def test_inr_precision_is_enforced_without_rounding():
    with pytest.raises(PersonalPowerRuleError):
        DuplicateCandidate(
            transaction_id="tx-precise",
            amount=Decimal("1.001"),
            currency="INR",
            occurred_on=date(2026, 10, 1),
            possible_duplicate_of_id="tx-original",
            description="precision boundary",
        )


def test_unsupported_currency_is_rejected():
    with pytest.raises(PersonalPowerRuleError):
        base_input(currency="ZZZ")


def test_refunds_reduce_period_expense_but_not_essential_expense_basis():
    report = build_personal_power_report(base_input())
    assert report.net_expenses_after_refunds == Decimal("41000.00")
    assert report.essential_expenses == Decimal("30000.00")
    assert report.discretionary_expenses == Decimal("12000.00")


def test_quiet_period_produces_a_non_guarantee_information_finding():
    report = build_personal_power_report(base_input())
    assert any(item.code == "NO_HIGH_PRIORITY_SIGNAL" for item in report.findings)
    assert "not a guarantee" in next(
        item.explanation for item in report.findings if item.code == "NO_HIGH_PRIORITY_SIGNAL"
    )


def test_finding_dataclass_serializes_to_typed_api_response():
    from dataclasses import asdict

    from myeconomy.api.personal_power_schemas import PowerFindingResponse

    report = build_personal_power_report(base_input())
    finding = next(item for item in report.findings if item.code == "NO_HIGH_PRIORITY_SIGNAL")
    response = PowerFindingResponse.model_validate(asdict(finding))
    assert response.finding_id == finding.finding_id
    assert response.source_references == []
