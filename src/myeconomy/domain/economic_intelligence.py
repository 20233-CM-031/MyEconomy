"""Deterministic economic-intelligence kernel for AwnNORA.

This module is deliberately independent of HTTP, persistence, model SDKs and providers.
Meta models may propose extracted facts or plans; this module validates economic invariants.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from myeconomy.domain.money import currency_exponent, quantize_total

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EconomicRuleError(ValueError):
    """A supplied economic object violates a deterministic domain invariant."""


class InvoiceDisposition(StrEnum):
    CONSISTENT = "CONSISTENT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ABSTAIN = "ABSTAIN"


class InvoiceFindingCode(StrEnum):
    LINE_ARITHMETIC_MISMATCH = "LINE_ARITHMETIC_MISMATCH"
    SUBTOTAL_MISMATCH = "SUBTOTAL_MISMATCH"
    TOTAL_MISMATCH = "TOTAL_MISMATCH"
    DUE_DATE_BEFORE_ISSUE = "DUE_DATE_BEFORE_ISSUE"
    LOW_EXTRACTION_CONFIDENCE = "LOW_EXTRACTION_CONFIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    DUPLICATE_DOCUMENT = "DUPLICATE_DOCUMENT"
    UNUSUAL_INCREASE = "UNUSUAL_INCREASE"


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Pointer to a source region; no raw document text is copied into the domain result."""

    field_name: str
    document_sha256: str
    locator: str
    confidence: Decimal

    def __post_init__(self) -> None:
        if not self.field_name.strip() or len(self.field_name) > 80:
            raise EconomicRuleError("Evidence field_name must contain 1 to 80 characters.")
        if not _SHA256_RE.fullmatch(self.document_sha256):
            raise EconomicRuleError("Evidence document_sha256 must be a lowercase SHA-256 digest.")
        if not self.locator.strip() or len(self.locator) > 160:
            raise EconomicRuleError("Evidence locator must contain 1 to 160 characters.")
        if not self.confidence.is_finite() or not Decimal("0") <= self.confidence <= Decimal("1"):
            raise EconomicRuleError("Evidence confidence must be between 0 and 1.")


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    description: str
    quantity: Decimal
    unit_price: Decimal
    declared_total: Decimal
    evidence_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.description.strip() or len(self.description) > 256:
            raise EconomicRuleError("Invoice line description must contain 1 to 256 characters.")
        line_amounts = (
            ("quantity", self.quantity),
            ("unit_price", self.unit_price),
            ("declared_total", self.declared_total),
        )
        for name, value in line_amounts:
            if not value.is_finite() or value < 0:
                raise EconomicRuleError(f"Invoice line {name} must be finite and non-negative.")
        if self.quantity <= 0:
            raise EconomicRuleError("Invoice line quantity must be greater than zero.")


@dataclass(frozen=True, slots=True)
class PriorInvoice:
    provider_key: str
    currency: str
    issue_date: date
    total_due: Decimal

    def __post_init__(self) -> None:
        if not self.provider_key.strip():
            raise EconomicRuleError("Prior invoice provider_key is required.")
        currency_exponent(self.currency)
        if not self.total_due.is_finite() or self.total_due <= 0:
            raise EconomicRuleError("Prior invoice total_due must be finite and positive.")


@dataclass(frozen=True, slots=True)
class InvoiceReviewInput:
    invoice_id: str
    provider_key: str
    currency: str
    source_document_sha256: str
    issue_date: date
    due_date: date | None
    lines: tuple[InvoiceLine, ...]
    declared_subtotal: Decimal
    tax: Decimal
    fees: Decimal
    credits: Decimal
    declared_total_due: Decimal
    extraction_confidence: Decimal
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.invoice_id.strip() or len(self.invoice_id) > 128:
            raise EconomicRuleError("invoice_id must contain 1 to 128 characters.")
        if not self.provider_key.strip() or len(self.provider_key) > 128:
            raise EconomicRuleError("provider_key must contain 1 to 128 characters.")
        if not _SHA256_RE.fullmatch(self.source_document_sha256):
            raise EconomicRuleError("source_document_sha256 must be a lowercase SHA-256 digest.")
        try:
            currency_exponent(self.currency)
        except ValueError as exc:
            raise EconomicRuleError(str(exc)) from exc
        if not self.lines:
            raise EconomicRuleError("An invoice must contain at least one line item.")
        if not self.extraction_confidence.is_finite() or not Decimal(
            "0"
        ) <= self.extraction_confidence <= Decimal("1"):
            raise EconomicRuleError("Extraction confidence must be between 0 and 1.")
        invoice_amounts = (
            ("subtotal", self.declared_subtotal),
            ("tax", self.tax),
            ("fees", self.fees),
            ("credits", self.credits),
            ("total_due", self.declared_total_due),
        )
        for name, value in invoice_amounts:
            if not value.is_finite() or value < 0:
                raise EconomicRuleError(f"Invoice {name} must be finite and non-negative.")


@dataclass(frozen=True, slots=True)
class InvoiceFinding:
    code: InvoiceFindingCode
    severity: str
    message: str
    evidence_fields: tuple[str, ...] = ()
    expected_amount: Decimal | None = None
    observed_amount: Decimal | None = None


@dataclass(frozen=True, slots=True)
class InvoiceReviewResult:
    invoice_id: str
    currency: str
    disposition: InvoiceDisposition
    findings: tuple[InvoiceFinding, ...]
    source_document_sha256: str
    disclaimer: str = (
        "This is an evidence and arithmetic review, not proof of fraud, a legal violation, "
        "or a confirmed entitlement. Verify the source document and provider before acting."
    )


def review_invoice(
    invoice: InvoiceReviewInput,
    *,
    known_document_hashes: frozenset[str] = frozenset(),
    prior_invoices: tuple[PriorInvoice, ...] = (),
    confidence_threshold: Decimal = Decimal("0.82"),
    increase_ratio_threshold: Decimal = Decimal("0.20"),
    increase_absolute_threshold: Decimal = Decimal("100.00"),
) -> InvoiceReviewResult:
    """Check invoice arithmetic, source evidence, duplicates and comparable bill changes.

    Returns findings for a human to inspect. Never labels an invoice as fraud.
    """
    currency_exponent(invoice.currency)
    monetary_inputs = [
        invoice.declared_subtotal,
        invoice.tax,
        invoice.fees,
        invoice.credits,
        invoice.declared_total_due,
        *(line.unit_price for line in invoice.lines),
        *(line.declared_total for line in invoice.lines),
    ]
    if any(quantize_total(value, invoice.currency) != value for value in monetary_inputs):
        raise EconomicRuleError(
            "Invoice monetary fields exceed the currency's minor-unit precision."
        )
    findings: list[InvoiceFinding] = []
    required_fields = {"invoice_id", "provider", "currency", "issue_date", "total_due"}
    for index in range(1, len(invoice.lines) + 1):
        required_fields.update(
            {
                f"line[{index}].quantity",
                f"line[{index}].unit_price",
                f"line[{index}].total",
            }
        )
    evidenced_fields = {
        ref.field_name
        for ref in invoice.evidence
        if ref.document_sha256 == invoice.source_document_sha256
    }
    missing = tuple(sorted(required_fields - evidenced_fields))
    if missing:
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.MISSING_EVIDENCE,
                "HIGH",
                "Required extracted fields are not linked to evidence in the source document.",
                missing,
            )
        )

    weak_evidence = tuple(
        sorted(
            {
                ref.field_name
                for ref in invoice.evidence
                if ref.document_sha256 == invoice.source_document_sha256
                and ref.confidence < confidence_threshold
            }
        )
    )
    if invoice.extraction_confidence < confidence_threshold or weak_evidence:
        fields = weak_evidence or ("document_extraction",)
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.LOW_EXTRACTION_CONFIDENCE,
                "HIGH",
                (
                    "Extraction confidence is below the configured review threshold; "
                    "do not automate an external action."
                ),
                fields,
            )
        )

    if invoice.source_document_sha256 in known_document_hashes:
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.DUPLICATE_DOCUMENT,
                "HIGH",
                "This exact source document digest has already been observed.",
                ("document_hash",),
            )
        )

    line_sum = sum((line.declared_total for line in invoice.lines), Decimal("0"))
    line_sum = quantize_total(line_sum, invoice.currency)
    for index, line in enumerate(invoice.lines, start=1):
        computed_line = quantize_total(line.quantity * line.unit_price, invoice.currency)
        declared_line = quantize_total(line.declared_total, invoice.currency)
        if computed_line != declared_line:
            findings.append(
                InvoiceFinding(
                    InvoiceFindingCode.LINE_ARITHMETIC_MISMATCH,
                    "HIGH",
                    (
                        f"Invoice line {index} does not reconcile quantity × unit price "
                        "to its declared amount."
                    ),
                    (
                        f"line[{index}].quantity",
                        f"line[{index}].unit_price",
                        f"line[{index}].total",
                    ),
                    computed_line,
                    declared_line,
                )
            )

    declared_subtotal = quantize_total(invoice.declared_subtotal, invoice.currency)
    if line_sum != declared_subtotal:
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.SUBTOTAL_MISMATCH,
                "HIGH",
                "The sum of line items does not equal the declared subtotal.",
                ("line_items", "subtotal"),
                line_sum,
                declared_subtotal,
            )
        )

    expected_total = quantize_total(
        invoice.declared_subtotal + invoice.tax + invoice.fees - invoice.credits,
        invoice.currency,
    )
    declared_total = quantize_total(invoice.declared_total_due, invoice.currency)
    if expected_total != declared_total:
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.TOTAL_MISMATCH,
                "HIGH",
                "Subtotal + tax + fees − credits does not equal the declared amount due.",
                ("subtotal", "tax", "fees", "credits", "total_due"),
                expected_total,
                declared_total,
            )
        )

    if invoice.due_date is not None and invoice.due_date < invoice.issue_date:
        findings.append(
            InvoiceFinding(
                InvoiceFindingCode.DUE_DATE_BEFORE_ISSUE,
                "MEDIUM",
                "The due date precedes the issue date; verify the dates on the original document.",
                ("issue_date", "due_date"),
            )
        )

    comparable = [
        item
        for item in prior_invoices
        if item.provider_key == invoice.provider_key
        and item.currency.upper() == invoice.currency.upper()
        and item.issue_date < invoice.issue_date
        and (invoice.issue_date - item.issue_date).days <= 120
        and item.total_due > 0
    ]
    if comparable:
        previous = max(comparable, key=lambda item: item.issue_date)
        prior_total = quantize_total(previous.total_due, invoice.currency)
        delta = declared_total - prior_total
        ratio = delta / prior_total
        if delta > increase_absolute_threshold and ratio > increase_ratio_threshold:
            findings.append(
                InvoiceFinding(
                    InvoiceFindingCode.UNUSUAL_INCREASE,
                    "MEDIUM",
                    (
                        "The amount due is materially higher than the most recent comparable bill. "
                        "This is a review signal, not proof of an improper charge."
                    ),
                    ("previous_bill.total_due", "total_due"),
                    prior_total,
                    declared_total,
                )
            )

    objective_review_codes = {
        InvoiceFindingCode.LINE_ARITHMETIC_MISMATCH,
        InvoiceFindingCode.SUBTOTAL_MISMATCH,
        InvoiceFindingCode.TOTAL_MISMATCH,
        InvoiceFindingCode.DUE_DATE_BEFORE_ISSUE,
        InvoiceFindingCode.DUPLICATE_DOCUMENT,
        InvoiceFindingCode.UNUSUAL_INCREASE,
    }
    if any(item.code in objective_review_codes for item in findings):
        disposition = InvoiceDisposition.REVIEW_REQUIRED
    elif any(
        item.code
        in {
            InvoiceFindingCode.MISSING_EVIDENCE,
            InvoiceFindingCode.LOW_EXTRACTION_CONFIDENCE,
        }
        for item in findings
    ):
        disposition = InvoiceDisposition.ABSTAIN
    else:
        disposition = InvoiceDisposition.CONSISTENT

    return InvoiceReviewResult(
        invoice_id=invoice.invoice_id,
        currency=invoice.currency.upper(),
        disposition=disposition,
        findings=tuple(findings),
        source_document_sha256=invoice.source_document_sha256,
    )


@dataclass(frozen=True, slots=True)
class OfferCandidate:
    offer_id: str
    currency: str
    baseline_total_minor: int
    provider_price_minor: int
    sponsor_credit_minor: int = 0
    required_extra_spend_minor: int = 0
    one_time_fees_minor: int = 0
    recurring_extra_minor: int = 0
    recurring_months: int = 0
    switching_cost_minor: int = 0
    eligibility_confirmed: bool = False
    quality_compatible: bool = False
    user_constraints_satisfied: bool = False

    def __post_init__(self) -> None:
        if not self.offer_id.strip() or len(self.offer_id) > 128:
            raise EconomicRuleError("offer_id must contain 1 to 128 characters.")
        try:
            currency_exponent(self.currency)
        except ValueError as exc:
            raise EconomicRuleError(str(exc)) from exc
        amounts = (
            self.baseline_total_minor,
            self.provider_price_minor,
            self.sponsor_credit_minor,
            self.required_extra_spend_minor,
            self.one_time_fees_minor,
            self.recurring_extra_minor,
            self.switching_cost_minor,
        )
        if any(value < 0 for value in amounts):
            raise EconomicRuleError("Offer amounts must be non-negative integer minor units.")
        if self.baseline_total_minor <= 0 or self.provider_price_minor <= 0:
            raise EconomicRuleError("Baseline and provider price must be greater than zero.")
        if not 0 <= self.recurring_months <= 120:
            raise EconomicRuleError("recurring_months must be between 0 and 120.")
        if self.recurring_months == 0 and self.recurring_extra_minor != 0:
            raise EconomicRuleError("Recurring extra cost requires a positive recurring term.")


@dataclass(frozen=True, slots=True)
class OfferEvaluation:
    offer_id: str
    currency: str
    baseline_total_minor: int
    total_offer_cost_minor: int
    net_benefit_minor: int
    accepted: bool
    rejection_reasons: tuple[str, ...]


def evaluate_offer(candidate: OfferCandidate) -> OfferEvaluation:
    """Compute real net benefit and reject offers that fail conditions or cost more."""
    total_cost = (
        candidate.provider_price_minor
        - candidate.sponsor_credit_minor
        + candidate.required_extra_spend_minor
        + candidate.one_time_fees_minor
        + candidate.recurring_extra_minor * candidate.recurring_months
        + candidate.switching_cost_minor
    )
    # A credit cannot create a negative purchase cost; excess credit is not cash income.
    total_cost = max(0, total_cost)
    net = candidate.baseline_total_minor - total_cost
    reasons: list[str] = []
    if not candidate.eligibility_confirmed:
        reasons.append("eligibility_not_confirmed")
    if not candidate.quality_compatible:
        reasons.append("quality_or_service_not_comparable")
    if not candidate.user_constraints_satisfied:
        reasons.append("user_constraints_not_satisfied")
    if net <= 0:
        reasons.append("non_positive_net_benefit")
    return OfferEvaluation(
        offer_id=candidate.offer_id,
        currency=candidate.currency.upper(),
        baseline_total_minor=candidate.baseline_total_minor,
        total_offer_cost_minor=total_cost,
        net_benefit_minor=net,
        accepted=not reasons,
        rejection_reasons=tuple(reasons),
    )


@dataclass(frozen=True, slots=True)
class DemandSignal:
    """A minimal contribution signal; participant_id is never returned in aggregates."""

    participant_id: str
    cohort_key: str
    category: str
    quantity: int
    created_at: datetime
    consent_granted_at: datetime
    consent_expires_at: datetime
    consent_revoked_at: datetime | None = None
    environment: str = "SYNTHETIC"

    def __post_init__(self) -> None:
        if not self.participant_id or not self.cohort_key or not self.category:
            raise EconomicRuleError("Demand signal identity, cohort and category are required.")
        if self.quantity <= 0 or self.quantity > 1_000_000:
            raise EconomicRuleError("Demand signal quantity must be between 1 and 1,000,000.")
        for value in (self.created_at, self.consent_granted_at, self.consent_expires_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise EconomicRuleError("Demand signal timestamps must be timezone-aware.")
        if self.consent_revoked_at is not None and (
            self.consent_revoked_at.tzinfo is None or self.consent_revoked_at.utcoffset() is None
        ):
            raise EconomicRuleError("Consent revocation timestamp must be timezone-aware.")
        if self.environment not in {"SYNTHETIC", "SANDBOX", "LIVE"}:
            raise EconomicRuleError("Unknown demand signal environment.")


@dataclass(frozen=True, slots=True)
class DemandAggregate:
    cohort_key: str
    category: str
    participant_count: int | None
    total_quantity: int | None
    suppressed: bool
    environment: str


def aggregate_consented_demand(
    signals: Iterable[DemandSignal],
    *,
    as_of: datetime,
    minimum_cohort_size: int = 5,
    maximum_age: timedelta = timedelta(days=30),
) -> tuple[DemandAggregate, ...]:
    """Aggregate only fresh signals with valid event-time and currently active consent.

    This is a minimum-cohort disclosure gate, not a formal differential-privacy guarantee.
    Production release must also prevent differencing/overlapping queries and use an audited
    aggregation policy (and differential privacy where risk analysis requires it).
    """
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise EconomicRuleError("as_of must be timezone-aware.")
    if minimum_cohort_size < 2:
        raise EconomicRuleError("minimum_cohort_size must be at least 2.")
    if maximum_age <= timedelta(0):
        raise EconomicRuleError("maximum_age must be positive.")
    grouped: dict[tuple[str, str, str], dict[str, tuple[datetime, int]]] = defaultdict(dict)
    for signal in signals:
        created = signal.created_at.astimezone(UTC)
        granted = signal.consent_granted_at.astimezone(UTC)
        expires = signal.consent_expires_at.astimezone(UTC)
        now = as_of.astimezone(UTC)
        revoked = signal.consent_revoked_at.astimezone(UTC) if signal.consent_revoked_at else None
        if created > now or now - created > maximum_age:
            continue
        if not granted <= created < expires or now >= expires:
            continue
        if revoked is not None and revoked <= now:
            continue
        key = (signal.cohort_key, signal.category, signal.environment)
        # One participant contributes at most once per cohort/category/environment.
        prior = grouped[key].get(signal.participant_id)
        if prior is None or created > prior[0]:
            grouped[key][signal.participant_id] = (created, signal.quantity)

    results: list[DemandAggregate] = []
    for (cohort, category, environment), contributions in sorted(grouped.items()):
        count = len(contributions)
        if count < minimum_cohort_size:
            results.append(DemandAggregate(cohort, category, None, None, True, environment))
        else:
            results.append(
                DemandAggregate(
                    cohort,
                    category,
                    count,
                    sum(quantity for _, quantity in contributions.values()),
                    False,
                    environment,
                )
            )
    return tuple(results)


class ValueStatus(StrEnum):
    ESTIMATED = "ESTIMATED"
    ATTEMPTED = "ATTEMPTED"
    SIMULATED = "SIMULATED"
    PROVIDER_CONFIRMED = "PROVIDER_CONFIRMED"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class ValueEvent:
    idempotency_key: str
    currency: str
    gross_value_minor: int
    additional_cost_minor: int
    status: ValueStatus
    environment: str
    evidence_verified: bool
    settlement_verified: bool

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip():
            raise EconomicRuleError("Value event requires an idempotency key.")
        try:
            currency_exponent(self.currency)
        except ValueError as exc:
            raise EconomicRuleError(str(exc)) from exc
        if self.gross_value_minor < 0 or self.additional_cost_minor < 0:
            raise EconomicRuleError("Value event amounts must be non-negative minor units.")
        if self.environment not in {"SYNTHETIC", "SANDBOX", "LIVE"}:
            raise EconomicRuleError("Unknown value event environment.")


def verified_individual_value_created(events: Iterable[ValueEvent], *, currency: str) -> int:
    """Return verified LIVE value only; simulations/estimates are always excluded."""
    normalized = currency.upper()
    currency_exponent(normalized)
    seen: set[str] = set()
    total = 0
    for event in events:
        if event.idempotency_key in seen:
            raise EconomicRuleError("Duplicate value-event idempotency key.")
        seen.add(event.idempotency_key)
        if event.currency.upper() != normalized:
            raise EconomicRuleError("VIVC aggregation cannot mix currencies.")
        if (
            event.environment == "LIVE"
            and event.status == ValueStatus.VERIFIED
            and event.evidence_verified
            and event.settlement_verified
        ):
            total += event.gross_value_minor - event.additional_cost_minor
    return total


class MissionStatus(StrEnum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


_MISSION_TRANSITIONS: dict[MissionStatus, frozenset[MissionStatus]] = {
    MissionStatus.CREATED: frozenset(
        {MissionStatus.PLANNED, MissionStatus.CANCELLED, MissionStatus.FAILED}
    ),
    MissionStatus.PLANNED: frozenset(
        {MissionStatus.RUNNING, MissionStatus.CANCELLED, MissionStatus.FAILED}
    ),
    MissionStatus.RUNNING: frozenset(
        {
            MissionStatus.WAITING_APPROVAL,
            MissionStatus.SUCCEEDED,
            MissionStatus.PARTIAL,
            MissionStatus.FAILED,
            MissionStatus.CANCELLED,
        }
    ),
    MissionStatus.WAITING_APPROVAL: frozenset(
        {MissionStatus.RUNNING, MissionStatus.CANCELLED, MissionStatus.FAILED}
    ),
    MissionStatus.SUCCEEDED: frozenset(),
    MissionStatus.PARTIAL: frozenset(),
    MissionStatus.FAILED: frozenset(),
    MissionStatus.CANCELLED: frozenset(),
}


def transition_mission(current: MissionStatus, target: MissionStatus) -> MissionStatus:
    """Validate a mission transition for GENIEA; persistence/checkpointing is a later adapter."""
    if target not in _MISSION_TRANSITIONS[current]:
        raise EconomicRuleError(
            f"Mission transition {current.value} -> {target.value} is not allowed."
        )
    return target


def authorize_tool_execution(
    *,
    mutates_external_state: bool,
    approval_granted: bool,
    permission_scope_active: bool,
    idempotency_key: str | None,
    environment: str,
    adapter_environment: str,
) -> None:
    """Policy gate before a GENIEA tool call crosses the application boundary."""
    if environment not in {"SYNTHETIC", "SANDBOX", "LIVE"}:
        raise EconomicRuleError("Unknown tool execution environment.")
    if adapter_environment not in {"SYNTHETIC", "SANDBOX", "LIVE"}:
        raise EconomicRuleError("Unknown configured adapter environment.")
    if environment != adapter_environment:
        raise EconomicRuleError("Execution environment does not match the configured adapter.")
    if not permission_scope_active:
        raise EconomicRuleError("A currently active user permission scope is required.")
    if mutates_external_state:
        if not approval_granted:
            raise EconomicRuleError("External mutations require explicit user approval.")
        if not idempotency_key or not idempotency_key.strip():
            raise EconomicRuleError("External mutations require an idempotency key.")
