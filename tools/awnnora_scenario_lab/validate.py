#!/usr/bin/env python3
"""Validate the Scenario Lab's safety and economic invariants."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenario_lab/generated")
catalog = json.loads((ROOT / "scenario_catalog.json").read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
checks = Counter()
errors: list[str] = []
seen = set()
run_count = 0
templates_by_slug = {item["slug"]: item for item in catalog["templates"]}
for line_number, line in enumerate(
    (ROOT / "runs.jsonl").read_text(encoding="utf-8").splitlines(), start=1
):
    if not line.strip():
        continue
    row = json.loads(line)
    run_count += 1
    if row["run_id"] in seen:
        errors.append(f"duplicate run_id at line {line_number}")
    seen.add(row["run_id"])
    checks["synthetic_label"] += (
        row.get("data_class") == "SYNTHETIC_FIXTURE" and row.get("environment") == "SYNTHETIC"
    )
    checks["no_external_side_effects"] += row["expected_invariants"].get(
        "external_side_effects_performed"
    ) is False and all(not e["external_call_performed"] for e in row["events"])
    checks["vivc_never_claimed"] += (
        row.get("vivc_eligibility") is False and row.get("outcome_state") == "SIMULATED"
    )
    checks["integer_paise"] += row.get("money_unit") == "PAISE_INTEGER" and all(
        isinstance(v, int) for key, v in row["economic_context"].items() if key.endswith("_minor")
    )

    def minor_fields(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).endswith("_minor") and nested is not None:
                    yield nested
                yield from minor_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from minor_fields(nested)

    checks["all_minor_fields_integer"] += all(
        isinstance(v, int) and not isinstance(v, bool) for v in minor_fields(row)
    )
    template = templates_by_slug.get(row["scenario_slug"], {})
    checks["run_matches_catalog"] += (
        row["scenario_id"] == template.get("scenario_id")
        and row["expected_decision"] == template.get("expected_decision")
        and [event["event"] for event in row["events"]] == template.get("event_sequence")
    )
    if row["category"] == "COMMONS":
        consent_ok = (
            row["scenario_inputs"]["commons_consent_granted"] is True
            or row["expected_decision"] == "EXCLUDE_REVOKED_SIGNAL"
        )
        checks["commons_consent_and_privacy"] += (
            row["expected_invariants"]["commons_consent_required"] is True
            and row["scenario_inputs"]["raw_private_financial_records_shared"] is False
            and consent_ok
        )
        suppressed_decisions = {
            "SUPPRESS_OUTPUT",
            "EXCLUDE_REVOKED_SIGNAL",
            "BLOCK_QUERY_AND_AUDIT",
            "REJECT_NON_POSITIVE_NET_BENEFIT",
        }
        cohort_ok = (
            row["scenario_inputs"]["commons_participant_count"]
            >= row["scenario_inputs"]["commons_minimum_cohort"]
            or row["expected_decision"] in suppressed_decisions
        )
        if row["expected_decision"] == "RELEASE_MINIMIZED_AGGREGATE":
            cohort_ok = cohort_ok and row["scenario_inputs"]["commons_consent_granted"] is True
        checks["commons_quorum_policy"] += cohort_ok
    if row["scenario_slug"] == "negative_net_offer":
        checks["negative_offer_rejected"] += (
            row["scenario_inputs"]["offer_net_benefit_minor"] <= 0
            and row["expected_decision"] == "REJECT_NON_POSITIVE_NET_BENEFIT"
        )
    if row["scenario_slug"] == "scholarship_possible_missing_documents":
        checks["no_false_award"] += (
            row["scenario_inputs"]["official_award_confirmed"] is False
            and row["scenario_inputs"]["eligibility_status"] != "APPROVED"
        )
    if row["scenario_slug"] == "private_edge_not_shareable":
        checks["private_edge_not_shared"] += (
            row["scenario_inputs"]["private_edge_shareable"] is False
            and row["expected_invariants"]["commons_raw_financial_data_exposed"] is False
            and row["scenario_inputs"]["raw_private_financial_records_shared"] is False
        )
    if row["scenario_slug"] == "gig_income_after_costs":
        checks["opportunity_net_economics"] += (
            row["scenario_inputs"]["opportunity_net_income_minor"]
            == row["scenario_inputs"]["opportunity_gross_income_minor"]
            - row["scenario_inputs"]["opportunity_direct_costs_minor"]
        )
    if row["scenario_slug"] == "low_quality_job_offer":
        checks["unsafe_opportunity_not_accepted"] += (
            row["scenario_inputs"]["opportunity_quality_and_safety_compatible"] is False
        )
    if row["scenario_slug"] == "inventory_margin_below_cost":
        checks["enterprise_below_cost_blocked"] += (
            row["scenario_inputs"]["enterprise_margin_minor"] < 0
            and row["expected_decision"] == "BLOCK_UNPROFITABLE_PRICE"
        )
    if row["scenario_slug"] == "stale_scheme_source":
        checks["stale_entitlement_abstains"] += (
            row["scenario_inputs"]["authoritative_source_current"] is False
        )
    if row["category"] == "CRISIS":
        checks["no_reflexive_new_debt"] += row["scenario_inputs"]["new_debt_recommended"] is False
    if row["category"] == "GENIEA":
        checks["agent_has_idempotency"] += all(
            bool(e.get("idempotency_key")) for e in row["events"]
        )
        checks["agent_human_gate"] += (
            row["expected_invariants"]["human_approval_before_consequential_action"] is True
        )
    # No real identifiers are part of the generated schema by construction.
    forbidden = {
        "aadhaar",
        "aadhaar_number",
        "pan",
        "pan_number",
        "upi_pin",
        "card_pan",
        "bank_password",
        "phone",
        "email",
        "full_address",
        "account_number",
        "password",
        "bearer_token",
    }

    def all_keys(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                yield str(key).lower()
                yield from all_keys(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from all_keys(nested)

    checks["no_sensitive_identifier_keys"] += not (forbidden & set(all_keys(row)))
    checks["specialized_case_invariants"] += (
        (
            row["scenario_slug"] != "invoice_line_arithmetic_mismatch"
            or row["scenario_inputs"]["line_quantity"]
            * row["scenario_inputs"]["line_unit_price_minor"]
            != row["scenario_inputs"]["line_declared_total_minor"]
        )
        and (
            row["scenario_slug"] != "provider_price_jump"
            or row["scenario_inputs"]["current_bill_minor"]
            > row["scenario_inputs"]["previous_bill_minor"]
        )
        and (
            row["scenario_slug"] != "resume_after_late_failure"
            or row["scenario_inputs"]["last_valid_checkpoint"]
            < row["scenario_inputs"]["mission_failure_step"]
        )
        and (
            row["scenario_slug"] != "approval_revoked_before_execute"
            or row["scenario_inputs"]["approval_active_at_execution"] is False
        )
    )

expected = manifest["run_count"]
checks["run_count_matches_manifest"] = run_count == expected == catalog["run_count"]
checks["template_count_matches_manifest"] = (
    len(catalog["templates"]) == manifest["scenario_template_count"]
)
checks["unique_scenario_slugs"] = len(templates_by_slug) == len(catalog["templates"])
checks["unique_run_ids"] = len(seen) == run_count
result = {
    "passed": not errors and all(checks.values()),
    "run_count": run_count,
    "template_count": len(catalog["templates"]),
    "checks": dict(checks),
    "errors": errors,
}
(ROOT / "validation_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
if not result["passed"]:
    raise SystemExit(1)
