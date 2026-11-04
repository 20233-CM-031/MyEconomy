#!/usr/bin/env python3
"""Generate a deterministic, synthetic AwnNORA scenario workload.

The output is a simulation fixture pack, not a production event stream or user dataset.
All monetary amounts are integer paise (INR minor units). No real names, contact details,
account identifiers, credentials, precise addresses, or provider endpoints are generated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

AS_OF = "2026-11-04"
SEED_DEFAULT = 20261104

# Each template is a product-level test story, not a claim that the capability is live.
TEMPLATES = [
    (
        "PERSONAL",
        "first_session_without_bank_link",
        "First useful session with manual context",
        "PERSONAL_POWER_REPORT",
        "READ_ONLY_REPORT",
        True,
        False,
    ),
    (
        "PERSONAL",
        "uncertain_income_classification",
        "Unclassified credits are not silently treated as salary",
        "FINANCIAL_DATA",
        "ASK_USER_TO_CLASSIFY",
        True,
        False,
    ),
    (
        "PERSONAL",
        "essential_outflow_deficit",
        "Essential commitments exceed classified inflow",
        "CRISIS_SHIELD",
        "PRIORITIZE_ESSENTIALS_AND_RELIEF",
        True,
        False,
    ),
    (
        "PERSONAL",
        "possible_duplicate_charge",
        "Potential duplicate is reviewed, not counted as recovery",
        "GUARDIAN",
        "REQUEST_USER_VERIFICATION",
        True,
        False,
    ),
    (
        "GUARDIAN",
        "provider_price_jump",
        "Comparable invoice amount materially increases",
        "GUARDIAN",
        "EVIDENCE_LINKED_REVIEW",
        True,
        False,
    ),
    (
        "GUARDIAN",
        "invoice_line_arithmetic_mismatch",
        "Quantity multiplied by unit price differs from line total",
        "GUARDIAN",
        "FLAG_ARITHMETIC_MISMATCH",
        True,
        False,
    ),
    (
        "GUARDIAN",
        "weak_extraction_confidence",
        "Low-confidence extraction must abstain",
        "GUARDIAN",
        "ABSTAIN_AND_REQUEST_REVIEW",
        True,
        False,
    ),
    (
        "GUARDIAN",
        "prompt_injection_in_document",
        "Invoice text attempts to instruct the model to exfiltrate data",
        "GUARDIAN",
        "IGNORE_DOCUMENT_INSTRUCTIONS",
        True,
        False,
    ),
    (
        "GUARDIAN",
        "mime_signature_mismatch",
        "Declared file type differs from file signature",
        "GUARDIAN",
        "REJECT_UPLOAD",
        True,
        False,
    ),
    (
        "ENTITLEMENT",
        "scholarship_possible_missing_documents",
        "Potential scheme match with missing proof",
        "ENTITLEMENTS",
        "LIST_GAPS_NOT_AWARD",
        True,
        False,
    ),
    (
        "ENTITLEMENT",
        "employer_reimbursement_deadline",
        "Reimbursement deadline approaching",
        "ENTITLEMENTS",
        "PREPARE_USER_CHECKLIST",
        True,
        False,
    ),
    (
        "ENTITLEMENT",
        "insurance_claim_evidence_gap",
        "Claim pathway needs policy and incident evidence",
        "ENTITLEMENTS",
        "REQUEST_MISSING_EVIDENCE",
        True,
        False,
    ),
    (
        "ENTITLEMENT",
        "stale_scheme_source",
        "Official eligibility source is out of date",
        "ENTITLEMENTS",
        "MARK_STALE_AND_ABSTAIN",
        True,
        False,
    ),
    (
        "OPPORTUNITY",
        "tutor_capacity_to_demand",
        "Available tutor hours match a verified demand brief",
        "OPPORTUNITY",
        "PREPARE_OPT_IN_PROPOSAL",
        True,
        False,
    ),
    (
        "OPPORTUNITY",
        "artisan_skill_needs_proof",
        "Capability is plausible but portfolio evidence is missing",
        "OPPORTUNITY",
        "REQUEST_PORTFOLIO_EVIDENCE",
        True,
        False,
    ),
    (
        "OPPORTUNITY",
        "gig_income_after_costs",
        "Gig opportunity is evaluated after travel and platform costs",
        "OPPORTUNITY",
        "RANK_BY_NET_VALUE",
        True,
        False,
    ),
    (
        "OPPORTUNITY",
        "low_quality_job_offer",
        "Headline pay hides unsafe hours or incompatible terms",
        "OPPORTUNITY",
        "REJECT_OR_ESCALATE_CONSTRAINT",
        True,
        False,
    ),
    (
        "RESOURCE_EXCHANGE",
        "idle_equipment_match",
        "Idle equipment matches a time-bounded local need",
        "RESOURCE_EXCHANGE",
        "REQUEST_BOTH_PARTY_CONFIRMATION",
        True,
        False,
    ),
    (
        "RESOURCE_EXCHANGE",
        "school_transport_capacity",
        "Unused transport seats match a school route need",
        "RESOURCE_EXCHANGE",
        "CHECK_SAFETY_AND_AVAILABILITY",
        True,
        False,
    ),
    (
        "RESOURCE_EXCHANGE",
        "surplus_produce_expiry",
        "Perishable supply must match before its safe-use window",
        "RESOURCE_EXCHANGE",
        "MATCH_WITH_EXPIRY_CONSTRAINT",
        True,
        False,
    ),
    (
        "CRISIS",
        "salary_delay_essential_priority",
        "Delayed salary with rent and food commitments",
        "CRISIS_SHIELD",
        "TRIAGE_ESSENTIALS_AND_RELIEF",
        True,
        False,
    ),
    (
        "CRISIS",
        "medical_shock_replan",
        "Unexpected medical expense disrupts the plan",
        "CRISIS_SHIELD",
        "REPLAN_AND_FIND_LEGITIMATE_SUPPORT",
        True,
        False,
    ),
    (
        "CRISIS",
        "multiple_emi_pressure",
        "Several debt obligations create pressure",
        "CRISIS_SHIELD",
        "SEEK_MORATORIUM_OR_RELIEF_NOT_NEW_DEBT",
        True,
        False,
    ),
    (
        "CRISIS",
        "utility_disconnection_notice",
        "Utility notice has a deadline and disputed amount",
        "CRISIS_SHIELD",
        "VERIFY_NOTICE_AND_CONTACT_OPTIONS",
        True,
        False,
    ),
    (
        "ONE_PERSON_ENTERPRISE",
        "baker_unit_economics",
        "Baker checks ingredient, packaging, time and delivery cost",
        "ONE_PERSON_ENTERPRISE",
        "PRICE_ABOVE_FULL_COST",
        True,
        False,
    ),
    (
        "ONE_PERSON_ENTERPRISE",
        "repair_technician_quote",
        "Technician prepares a transparent estimate",
        "ONE_PERSON_ENTERPRISE",
        "DRAFT_QUOTE_FOR_APPROVAL",
        True,
        False,
    ),
    (
        "ONE_PERSON_ENTERPRISE",
        "tailor_catalogue_order",
        "Tailor moves from catalogue enquiry to order tracking",
        "ONE_PERSON_ENTERPRISE",
        "CREATE_DRAFT_ORDER",
        True,
        False,
    ),
    (
        "ONE_PERSON_ENTERPRISE",
        "inventory_margin_below_cost",
        "Price is lower than variable and fulfilment costs",
        "ONE_PERSON_ENTERPRISE",
        "BLOCK_UNPROFITABLE_PRICE",
        True,
        False,
    ),
    (
        "COMMONS",
        "consented_quorum_reached",
        "Purpose-consented demand reaches a minimum cohort",
        "COMMONS",
        "RELEASE_MINIMIZED_AGGREGATE",
        True,
        True,
    ),
    (
        "COMMONS",
        "below_quorum_suppressed",
        "Cohort is too small for aggregate release",
        "COMMONS",
        "SUPPRESS_OUTPUT",
        True,
        True,
    ),
    (
        "COMMONS",
        "consent_revoked_before_use",
        "A participant revokes before a future aggregation",
        "COMMONS",
        "EXCLUDE_REVOKED_SIGNAL",
        True,
        True,
    ),
    (
        "COMMONS",
        "differencing_attack_attempt",
        "Repeated narrow queries could infer one participant",
        "COMMONS",
        "BLOCK_QUERY_AND_AUDIT",
        True,
        True,
    ),
    (
        "COMMONS",
        "negative_net_offer",
        "Discount is erased by incremental spend and fees",
        "COMMONS",
        "REJECT_NON_POSITIVE_NET_BENEFIT",
        True,
        True,
    ),
    (
        "GENIEA",
        "resume_after_late_failure",
        "Long mission resumes from a verified checkpoint",
        "GENIEA",
        "RESUME_WITHOUT_REPLAY",
        True,
        False,
    ),
    (
        "GENIEA",
        "external_timeout_reconcile",
        "Provider times out after a possible side effect",
        "GENIEA",
        "RECONCILE_BEFORE_RETRY",
        True,
        False,
    ),
    (
        "GENIEA",
        "approval_revoked_before_execute",
        "Approval is revoked before the tool runs",
        "GENIEA",
        "BLOCK_MUTATION",
        True,
        False,
    ),
    (
        "GENIEA",
        "duplicate_step_delivery",
        "A worker receives the same step twice",
        "GENIEA",
        "IDEMPOTENT_REPLAY",
        True,
        False,
    ),
    (
        "KRN",
        "stale_knowledge_source",
        "Public scheme/provider terms have expired",
        "KRN",
        "MARK_STALE_AND_RETRIEVE_CURRENT_SOURCE",
        True,
        False,
    ),
    (
        "KRN",
        "evidence_span_hash_mismatch",
        "Evidence locator points to a different document digest",
        "KRN",
        "REJECT_PROVENANCE_LINK",
        True,
        False,
    ),
    (
        "KRN",
        "private_edge_not_shareable",
        "Private household relationship is queried by Commons",
        "KRN",
        "DENY_PRIVATE_EDGE",
        True,
        True,
    ),
    (
        "VIVC",
        "synthetic_estimate_not_counted",
        "A model estimates possible savings in a demo",
        "VIVC",
        "EXCLUDE_FROM_VERIFIED_VALUE",
        True,
        False,
    ),
    (
        "VIVC",
        "provider_confirmed_not_settled",
        "Provider acknowledges a refund but settlement is not observed",
        "VIVC",
        "KEEP_PENDING_NOT_VERIFIED",
        True,
        False,
    ),
    (
        "VIVC",
        "live_settlement_idempotent",
        "A live outcome is verified once after settlement and evidence",
        "VIVC",
        "COUNT_NET_VALUE_ONCE",
        True,
        False,
    ),
    (
        "OPERATIONS",
        "cross_tenant_access_attempt",
        "User attempts to read another owner's case",
        "SECURITY",
        "DENY_AND_AUDIT",
        True,
        False,
    ),
    (
        "OPERATIONS",
        "partner_api_outage",
        "Approved partner API is unavailable",
        "INTEGRATIONS",
        "QUEUE_SAFE_RETRY_NO_DUPLICATE",
        True,
        False,
    ),
    (
        "OPERATIONS",
        "export_and_erasure_request",
        "User requests data export then erasure",
        "PRIVACY",
        "VERIFY_IDENTITY_AND_RETENTION_RULES",
        True,
        False,
    ),
]

EVENTS = {
    "PERSONAL": [
        "INTAKE_RECEIVED",
        "OWNER_SCOPE_RESOLVED",
        "DETERMINISTIC_ANALYSIS",
        "REPORT_PRESENTED",
    ],
    "GUARDIAN": [
        "DOCUMENT_RECEIVED",
        "QUARANTINE_OR_VALIDATE",
        "EVIDENCE_REVIEW",
        "HUMAN_DECISION_REQUIRED",
    ],
    "ENTITLEMENT": [
        "SOURCE_VERSION_CHECK",
        "ELIGIBILITY_RULES_EVALUATED",
        "MISSING_EVIDENCE_LISTED",
        "NO_AWARD_ASSUMED",
    ],
    "OPPORTUNITY": [
        "CAPABILITY_PROFILE_READ",
        "DEMAND_MATCHED",
        "NET_VALUE_AND_CONSTRAINTS_CHECKED",
        "USER_OPT_IN_REQUIRED",
    ],
    "RESOURCE_EXCHANGE": [
        "CAPACITY_LISTED",
        "DEMAND_MATCHED",
        "SAFETY_AND_AVAILABILITY_CHECKED",
        "BOTH_PARTIES_CONFIRM",
    ],
    "CRISIS": [
        "SHOCK_DETECTED",
        "ESSENTIALS_PRIORITIZED",
        "RELIEF_AND_SUPPORT_SEARCHED",
        "NO_AUTOMATIC_DEBT_PUSH",
    ],
    "ONE_PERSON_ENTERPRISE": [
        "COSTS_CAPTURED",
        "UNIT_ECONOMICS_COMPUTED",
        "DRAFT_COMMERCIAL_ARTIFACT",
        "USER_APPROVAL_REQUIRED",
    ],
    "COMMONS": [
        "PURPOSE_CONSENT_CHECKED",
        "MINIMIZED_SIGNAL_VALIDATED",
        "PRIVACY_AND_QUORUM_GATE",
        "AGGREGATE_RELEASE_OR_SUPPRESS",
    ],
    "GENIEA": ["MISSION_PLANNED", "STEP_CLAIMED", "CHECKPOINT_WRITTEN", "RECONCILE_OR_RESUME"],
    "KRN": [
        "SOURCE_INGESTED",
        "PROVENANCE_VALIDATED",
        "TEMPORAL_VALIDITY_CHECKED",
        "PRIVATE_PUBLIC_BOUNDARY_ENFORCED",
    ],
    "VIVC": ["VALUE_CLAIM_CREATED", "EVIDENCE_CHECKED", "SETTLEMENT_CHECKED", "COUNT_OR_EXCLUDE"],
    "OPERATIONS": [
        "REQUEST_AUTHENTICATED",
        "SCOPE_CHECKED",
        "FAILURE_OR_ACTION_RECORDED",
        "AUDIT_TRAIL_WRITTEN",
    ],
}


def generate(out: Path, replicas: int, seed: int) -> dict:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    catalog = []
    runs_path = out / "runs.jsonl"
    total = 0
    with runs_path.open("w", encoding="utf-8", newline="\n") as stream:
        for index, (
            category,
            slug,
            title,
            capability,
            expected,
            human_control,
            commons,
        ) in enumerate(TEMPLATES, start=1):
            sid = f"SCN-{index:03d}"
            template = {
                "scenario_id": sid,
                "slug": slug,
                "category": category,
                "title": title,
                "capability": capability,
                "expected_decision": expected,
                "human_control_required": human_control,
                "commons_consent_required": commons,
                "external_side_effects_in_fixture": False,
                "synthetic_only": True,
                "event_sequence": EVENTS[category],
            }
            catalog.append(template)
            for replica in range(1, replicas + 1):
                persona = f"SYN-PER-{index:03d}-{replica:05d}"
                income = rng.randrange(2500, 18001) * 1000  # paise: ₹25,000–₹1,80,000
                essential_ratio = rng.randrange(42, 96)
                essential = income * essential_ratio // 100
                discretionary = rng.randrange(0, max(1, income // 3))
                shock = rng.randrange(0, 4001) * 100
                # Purpose-built edge cases are not left to random chance.
                if slug in {"essential_outflow_deficit", "multiple_emi_pressure"}:
                    income, essential, discretionary = 5_000_000, 4_600_000, 1_100_000
                if slug == "salary_delay_essential_priority":
                    income, essential, discretionary = 0, 3_200_000, 450_000
                if slug == "medical_shock_replan":
                    income, essential, discretionary, shock = (
                        6_500_000,
                        4_000_000,
                        800_000,
                        2_800_000,
                    )
                if slug == "uncertain_income_classification":
                    income = 0  # unknown credits remain unclassified, never inferred as salary
                if slug == "inventory_margin_below_cost":
                    discretionary = max(discretionary, 1)
                cohort = rng.choice(
                    [
                        "HYD-CLUSTER-A",
                        "HYD-CLUSTER-B",
                        "PUNE-CLUSTER-A",
                        "JAIPUR-CLUSTER-C",
                        "INDORE-CLUSTER-B",
                    ]
                )
                participant_count = (
                    5
                    if slug == "consented_quorum_reached"
                    else (4 if slug == "below_quorum_suppressed" else rng.randrange(3, 9))
                )
                offer_baseline = rng.randrange(800, 5001) * 100
                offer_cost = offer_baseline + rng.randrange(-500, 1001) * 100
                if slug == "negative_net_offer":
                    offer_cost = offer_baseline + rng.randrange(100, 501) * 100
                offer_net = offer_baseline - offer_cost
                extraction_confidence = round(rng.uniform(0.35, 0.99), 3)
                if slug == "weak_extraction_confidence":
                    extraction_confidence = round(rng.uniform(0.25, 0.70), 3)
                if slug == "scholarship_possible_missing_documents":
                    eligibility_status = "POTENTIAL_MATCH_MISSING_DOCUMENTS"
                else:
                    eligibility_status = "NOT_AUTHORITY_CONFIRMED"
                value_state = "SYNTHETIC_FIXTURE_ONLY"
                opportunity_gross = 8_000_000 if slug == "gig_income_after_costs" else 4_500_000
                opportunity_costs = 3_200_000 if slug == "gig_income_after_costs" else 900_000
                enterprise_price = 65_000
                enterprise_full_cost = 68_000 if slug == "inventory_margin_below_cost" else 52_000
                run = {
                    "run_id": f"RUN-{index:03d}-{replica:05d}",
                    "scenario_id": sid,
                    "scenario_slug": slug,
                    "category": category,
                    "persona_id": persona,
                    "replica": replica,
                    "seed": seed,
                    "as_of_date": AS_OF,
                    "currency": "INR",
                    "money_unit": "PAISE_INTEGER",
                    "economic_context": {
                        "monthly_income_minor": income,
                        "monthly_essential_outflow_minor": essential,
                        "monthly_discretionary_outflow_minor": discretionary,
                        "unexpected_shock_minor": shock,
                        "household_size": rng.randint(1, 7),
                        "broad_locality_cluster": cohort,
                    },
                    "scenario_inputs": {
                        "extraction_confidence": extraction_confidence,
                        "document_hash_matches": slug != "evidence_span_hash_mismatch",
                        "document_prompt_injection_present": slug == "prompt_injection_in_document",
                        "declared_mime_matches_signature": slug != "mime_signature_mismatch",
                        "previous_bill_minor": 800_00 if slug == "provider_price_jump" else None,
                        "current_bill_minor": 1180_00 if slug == "provider_price_jump" else None,
                        "line_quantity": 2 if slug == "invoice_line_arithmetic_mismatch" else 1,
                        "line_unit_price_minor": 750_00
                        if slug == "invoice_line_arithmetic_mismatch"
                        else 100_00,
                        "line_declared_total_minor": 1600_00
                        if slug == "invoice_line_arithmetic_mismatch"
                        else 100_00,
                        "commons_participant_count": participant_count,
                        "commons_minimum_cohort": 5,
                        "private_edge_shareable": False
                        if slug == "private_edge_not_shareable"
                        else None,
                        "commons_consent_granted": slug not in {"consent_revoked_before_use"},
                        "raw_private_financial_records_shared": False,
                        "offer_baseline_minor": offer_baseline,
                        "offer_total_cost_minor": offer_cost,
                        "offer_net_benefit_minor": offer_net,
                        "eligibility_status": eligibility_status,
                        "official_award_confirmed": False,
                        "authoritative_source_current": slug != "stale_scheme_source",
                        "scheme_deadline_days": 3
                        if slug == "employer_reimbursement_deadline"
                        else None,
                        "new_debt_recommended": False,
                        "skill_evidence_state": "MISSING"
                        if slug == "artisan_skill_needs_proof"
                        else "AVAILABLE",
                        "available_hours_per_week": 8
                        if slug == "tutor_capacity_to_demand"
                        else rng.randrange(2, 21),
                        "opportunity_gross_income_minor": opportunity_gross,
                        "opportunity_direct_costs_minor": opportunity_costs,
                        "opportunity_net_income_minor": opportunity_gross - opportunity_costs,
                        "opportunity_quality_and_safety_compatible": slug
                        != "low_quality_job_offer",
                        "estimated_delivery_cost_minor": rng.randrange(100, 1201) * 100,
                        "resource_safe_window_hours": 18
                        if slug == "surplus_produce_expiry"
                        else 72,
                        "both_resource_parties_confirmed": False,
                        "enterprise_sale_price_minor": enterprise_price,
                        "enterprise_full_cost_minor": enterprise_full_cost,
                        "enterprise_margin_minor": enterprise_price - enterprise_full_cost,
                        "value_evidence_verified": slug == "live_settlement_idempotent",
                        "provider_settlement_verified": slug == "live_settlement_idempotent",
                        "mission_failure_step": 4 if slug == "resume_after_late_failure" else None,
                        "last_valid_checkpoint": 3 if slug == "resume_after_late_failure" else None,
                        "provider_side_effect_state": "UNKNOWN_REQUIRES_RECONCILIATION"
                        if slug == "external_timeout_reconcile"
                        else "NO_SIDE_EFFECT",
                        "approval_active_at_execution": slug != "approval_revoked_before_execute",
                        "outcome_state_fixture": "PROVIDER_CONFIRMED_NOT_SETTLED"
                        if slug == "provider_confirmed_not_settled"
                        else value_state,
                    },
                    "expected_decision": expected,
                    "expected_invariants": {
                        "owner_scope_enforced": True,
                        "deterministic_money_only": True,
                        "human_approval_before_consequential_action": human_control,
                        "commons_consent_required": commons,
                        "commons_raw_financial_data_exposed": False,
                        "synthetic_value_counted_as_live_vivc": False,
                        "external_side_effects_performed": False,
                        "idempotency_or_reconciliation_required": category == "GENIEA"
                        or slug == "partner_api_outage",
                    },
                    "outcome_state": "SIMULATED",
                    "vivc_eligibility": False,
                    "environment": "SYNTHETIC",
                    "data_class": "SYNTHETIC_FIXTURE",
                    "events": [
                        {
                            "sequence": seq,
                            "offset": f"T+{seq - 1}",
                            "event": event,
                            "actor": "SYSTEM_OR_SYNTHETIC_USER",
                            "state": "SIMULATED",
                            "idempotency_key": f"{persona}:{slug}:{seq}",
                            "external_call_performed": False,
                        }
                        for seq, event in enumerate(EVENTS[category], start=1)
                    ],
                }
                # Make a revoked Commons contribution explicitly unavailable.
                if slug == "consent_revoked_before_use":
                    run["scenario_inputs"]["commons_consent_granted"] = False
                # Late agent failure is deliberately after a simulated checkpoint.
                if slug == "resume_after_late_failure":
                    run["scenario_inputs"]["failure_step"] = 4
                    run["scenario_inputs"]["last_valid_checkpoint"] = 3
                line = json.dumps(run, sort_keys=True, separators=(",", ":"))
                stream.write(line + "\n")
                total += 1
    catalog_path = out / "scenario_catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "dataset": "AwnNORA Scenario Lab",
                "version": "1.0.0",
                "synthetic_only": True,
                "as_of_date": AS_OF,
                "scenario_template_count": len(catalog),
                "replicas_per_template": replicas,
                "run_count": total,
                "templates": catalog,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    hashes = {}
    for p in (catalog_path, runs_path):
        hashes[p.name] = {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
    manifest = {
        "dataset": "AwnNORA Scenario Lab",
        "version": "1.0.0",
        "synthetic_only": True,
        "seed": seed,
        "scenario_template_count": len(catalog),
        "run_count": total,
        "data_class": "SYNTHETIC_FIXTURE",
        "money_unit": "PAISE_INTEGER",
        "external_side_effects": False,
        "files": hashes,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("scenario_lab/generated"))
    parser.add_argument("--replicas", type=int, default=25, help="Runs per scenario template")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = parser.parse_args()
    if args.replicas < 1 or args.replicas > 10000:
        raise SystemExit("--replicas must be between 1 and 10000")
    print(json.dumps(generate(args.out, args.replicas, args.seed), indent=2))


if __name__ == "__main__":
    main()
