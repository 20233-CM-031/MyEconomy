from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from myeconomy.domain.economic_intelligence import (
    DemandSignal,
    EconomicRuleError,
    EvidenceRef,
    InvoiceDisposition,
    InvoiceFindingCode,
    InvoiceLine,
    InvoiceReviewInput,
    MissionStatus,
    OfferCandidate,
    PriorInvoice,
    ValueEvent,
    ValueStatus,
    aggregate_consented_demand,
    authorize_tool_execution,
    evaluate_offer,
    review_invoice,
    transition_mission,
    verified_individual_value_created,
)

DOC = "a" * 64
NOW = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)


def valid_invoice(**changes):
    evidence = tuple(
        EvidenceRef(field, DOC, f"page=1;field={field}", Decimal("0.99"))
        for field in (
            "invoice_id",
            "provider",
            "currency",
            "issue_date",
            "total_due",
            "line[1].quantity",
            "line[1].unit_price",
            "line[1].total",
        )
    )
    values = dict(
        invoice_id="INV-DEMO-01",
        provider_key="provider-demo-01",
        currency="INR",
        source_document_sha256=DOC,
        issue_date=date(2026, 10, 1),
        due_date=date(2026, 10, 20),
        lines=(InvoiceLine("Monthly service", Decimal("1"), Decimal("1000"), Decimal("1000")),),
        declared_subtotal=Decimal("1000"),
        tax=Decimal("180"),
        fees=Decimal("0"),
        credits=Decimal("0"),
        declared_total_due=Decimal("1180"),
        extraction_confidence=Decimal("0.99"),
        evidence=evidence,
    )
    values.update(changes)
    return InvoiceReviewInput(**values)


def test_invoice_consistent_arithmetic_and_evidence():
    result = review_invoice(valid_invoice())
    assert result.disposition == InvoiceDisposition.CONSISTENT
    assert result.findings == ()


def test_invoice_line_math_mismatch_is_review_required():
    invoice = valid_invoice(
        lines=(InvoiceLine("Service", Decimal("2"), Decimal("500"), Decimal("800")),)
    )
    result = review_invoice(invoice)
    assert result.disposition == InvoiceDisposition.REVIEW_REQUIRED
    assert InvoiceFindingCode.LINE_ARITHMETIC_MISMATCH in {f.code for f in result.findings}


def test_invoice_subtotal_and_total_mismatch_are_distinct():
    invoice = valid_invoice(declared_subtotal=Decimal("1100"), declared_total_due=Decimal("1200"))
    result = review_invoice(invoice)
    codes = {f.code for f in result.findings}
    assert InvoiceFindingCode.SUBTOTAL_MISMATCH in codes
    assert InvoiceFindingCode.TOTAL_MISMATCH in codes


def test_low_confidence_abstains_from_automatic_action():
    invoice = valid_invoice(extraction_confidence=Decimal("0.50"))
    result = review_invoice(invoice)
    assert result.disposition == InvoiceDisposition.ABSTAIN
    assert InvoiceFindingCode.LOW_EXTRACTION_CONFIDENCE in {f.code for f in result.findings}


def test_missing_required_evidence_abstains():
    invoice = valid_invoice(evidence=())
    result = review_invoice(invoice)
    assert result.disposition == InvoiceDisposition.ABSTAIN
    assert InvoiceFindingCode.MISSING_EVIDENCE in {f.code for f in result.findings}


def test_due_date_before_issue_requires_review():
    invoice = valid_invoice(due_date=date(2026, 9, 30))
    result = review_invoice(invoice)
    assert result.disposition == InvoiceDisposition.REVIEW_REQUIRED
    assert InvoiceFindingCode.DUE_DATE_BEFORE_ISSUE in {f.code for f in result.findings}


def test_exact_duplicate_document_is_flagged():
    result = review_invoice(valid_invoice(), known_document_hashes=frozenset({DOC}))
    assert InvoiceFindingCode.DUPLICATE_DOCUMENT in {f.code for f in result.findings}


def test_comparable_bill_increase_is_signal_not_fraud_claim():
    prior = (PriorInvoice("provider-demo-01", "INR", date(2026, 9, 1), Decimal("800")),)
    result = review_invoice(valid_invoice(), prior_invoices=prior)
    assert InvoiceFindingCode.UNUSUAL_INCREASE in {f.code for f in result.findings}
    assert "not proof" in result.disclaimer


def test_invoice_rejects_money_precision_beyond_currency_minor_unit():
    invoice = valid_invoice(tax=Decimal("180.001"))
    with pytest.raises(EconomicRuleError):
        review_invoice(invoice)


def test_bad_evidence_digest_rejected():
    with pytest.raises(EconomicRuleError):
        EvidenceRef("total_due", "bad", "page=1", Decimal("0.9"))


def offer(**changes):
    values = dict(
        offer_id="OFFER-1",
        currency="INR",
        baseline_total_minor=200_000,
        provider_price_minor=185_000,
        sponsor_credit_minor=10_000,
        required_extra_spend_minor=5_000,
        one_time_fees_minor=1_000,
        recurring_extra_minor=500,
        recurring_months=2,
        switching_cost_minor=0,
        eligibility_confirmed=True,
        quality_compatible=True,
        user_constraints_satisfied=True,
    )
    values.update(changes)
    return OfferCandidate(**values)


def test_offer_uses_total_cost_not_headline_discount():
    result = evaluate_offer(offer())
    assert result.total_offer_cost_minor == 182_000
    assert result.net_benefit_minor == 18_000
    assert result.accepted is True


def test_offer_rejected_when_extra_costs_make_net_value_negative():
    result = evaluate_offer(offer(required_extra_spend_minor=30_000, recurring_extra_minor=20_000))
    assert result.accepted is False
    assert "non_positive_net_benefit" in result.rejection_reasons


def test_offer_rejected_when_eligibility_unconfirmed_or_quality_mismatch():
    result = evaluate_offer(offer(eligibility_confirmed=False, quality_compatible=False))
    assert result.accepted is False
    assert "eligibility_not_confirmed" in result.rejection_reasons
    assert "quality_or_service_not_comparable" in result.rejection_reasons


def signal(
    user,
    *,
    revoked=None,
    expires=None,
    created=None,
    cohort="cohort-jaipur",
    category="education",
):
    created_at = created or NOW - timedelta(days=1)
    return DemandSignal(
        participant_id=user,
        cohort_key=cohort,
        category=category,
        quantity=1,
        created_at=created_at,
        consent_granted_at=created_at - timedelta(days=1),
        consent_expires_at=expires or NOW + timedelta(days=60),
        consent_revoked_at=revoked,
    )


def test_commons_aggregation_suppresses_small_cohorts():
    results = aggregate_consented_demand(
        [signal("u1"), signal("u2"), signal("u3")],
        as_of=NOW,
        minimum_cohort_size=5,
    )
    assert len(results) == 1
    assert results[0].suppressed is True
    assert results[0].participant_count is None
    assert results[0].total_quantity is None


def test_commons_aggregation_excludes_expired_consent():
    expired = [signal(f"u{i}", expires=NOW - timedelta(seconds=1)) for i in range(5)]
    assert aggregate_consented_demand(expired, as_of=NOW, minimum_cohort_size=5) == ()


def test_commons_aggregation_excludes_stale_signals():
    stale = [signal(f"u{i}", created=NOW - timedelta(days=45)) for i in range(5)]
    assert aggregate_consented_demand(stale, as_of=NOW, minimum_cohort_size=5) == ()


def test_commons_aggregation_reveals_only_cohort_aggregate_after_quorum():
    signals = [signal(f"u{i}") for i in range(5)]
    results = aggregate_consented_demand(signals, as_of=NOW, minimum_cohort_size=5)
    assert results[0].suppressed is False
    assert results[0].participant_count == 5
    assert results[0].total_quantity == 5
    assert not hasattr(results[0], "participant_ids")


def test_revoked_or_expired_consent_signal_is_excluded():
    signals = [signal(f"u{i}") for i in range(4)]
    signals.append(signal("u5", revoked=NOW - timedelta(hours=1)))
    results = aggregate_consented_demand(signals, as_of=NOW, minimum_cohort_size=5)
    assert results[0].suppressed is True


def test_signal_cannot_predate_consent():
    created = NOW - timedelta(days=1)
    bad = DemandSignal(
        participant_id="u1",
        cohort_key="c",
        category="food",
        quantity=1,
        created_at=created,
        consent_granted_at=created + timedelta(minutes=1),
        consent_expires_at=NOW + timedelta(days=10),
    )
    # Object is valid as a record; aggregator must exclude it by event-time consent.
    results = aggregate_consented_demand([bad], as_of=NOW, minimum_cohort_size=2)
    assert results == ()


def test_vivc_counts_only_verified_live_evidence_and_settlement():
    events = [
        ValueEvent("e1", "INR", 10_000, 1_000, ValueStatus.VERIFIED, "LIVE", True, True),
        ValueEvent("e2", "INR", 50_000, 0, ValueStatus.SIMULATED, "SYNTHETIC", True, True),
        ValueEvent("e3", "INR", 20_000, 0, ValueStatus.VERIFIED, "LIVE", False, True),
        ValueEvent("e4", "INR", 30_000, 0, ValueStatus.PROVIDER_CONFIRMED, "LIVE", True, False),
    ]
    assert verified_individual_value_created(events, currency="INR") == 9_000


def test_vivc_rejects_currency_mix_and_duplicate_keys():
    events = [
        ValueEvent("e1", "INR", 100, 0, ValueStatus.VERIFIED, "LIVE", True, True),
        ValueEvent("e1", "INR", 100, 0, ValueStatus.VERIFIED, "LIVE", True, True),
    ]
    with pytest.raises(EconomicRuleError):
        verified_individual_value_created(events, currency="INR")
    with pytest.raises(EconomicRuleError):
        verified_individual_value_created(
            [ValueEvent("e2", "USD", 100, 0, ValueStatus.VERIFIED, "LIVE", True, True)],
            currency="INR",
        )


def test_geniea_mission_transitions_are_bounded():
    assert transition_mission(MissionStatus.CREATED, MissionStatus.PLANNED) == MissionStatus.PLANNED
    assert (
        transition_mission(MissionStatus.RUNNING, MissionStatus.WAITING_APPROVAL)
        == MissionStatus.WAITING_APPROVAL
    )
    with pytest.raises(EconomicRuleError):
        transition_mission(MissionStatus.SUCCEEDED, MissionStatus.RUNNING)
    with pytest.raises(EconomicRuleError):
        transition_mission(MissionStatus.CREATED, MissionStatus.SUCCEEDED)


def test_geniea_mutating_tool_requires_approval_scope_and_idempotency():
    with pytest.raises(EconomicRuleError):
        authorize_tool_execution(
            mutates_external_state=True,
            approval_granted=False,
            permission_scope_active=True,
            idempotency_key="k",
            environment="SYNTHETIC",
            adapter_environment="SYNTHETIC",
        )
    with pytest.raises(EconomicRuleError):
        authorize_tool_execution(
            mutates_external_state=True,
            approval_granted=True,
            permission_scope_active=False,
            idempotency_key="k",
            environment="LIVE",
            adapter_environment="LIVE",
        )
    with pytest.raises(EconomicRuleError):
        authorize_tool_execution(
            mutates_external_state=True,
            approval_granted=True,
            permission_scope_active=True,
            idempotency_key=None,
            environment="LIVE",
            adapter_environment="LIVE",
        )
    authorize_tool_execution(
        mutates_external_state=True,
        approval_granted=True,
        permission_scope_active=True,
        idempotency_key="mission-1-step-1",
        environment="SYNTHETIC",
        adapter_environment="SYNTHETIC",
    )
    with pytest.raises(EconomicRuleError):
        authorize_tool_execution(
            mutates_external_state=False,
            approval_granted=False,
            permission_scope_active=True,
            idempotency_key=None,
            environment="SYNTHETIC",
            adapter_environment="LIVE",
        )
