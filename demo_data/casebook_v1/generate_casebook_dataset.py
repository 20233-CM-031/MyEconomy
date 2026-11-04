#!/usr/bin/env python3
"""Generate reproducible, clearly synthetic Personal Casebook lifecycle data."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20261104
STATUSES = [
    "OPEN",
    "IN_REVIEW",
    "ACTION_READY",
    "WAITING_FOR_USER",
    "WAITING_EXTERNAL",
    "RESOLVED",
    "CLOSED",
]
ENGINES = ["PERSONAL", "GUARDIAN", "OPPORTUNITY", "ENTITLEMENT", "CRISIS", "ENTERPRISE"]
SCENARIOS = [
    (
        "personal_duplicate_review",
        "PERSONAL",
        "OPEN",
        "Potential duplicate needs source comparison",
        "No double charge is confirmed.",
    ),
    (
        "personal_cashflow_review",
        "PERSONAL",
        "IN_REVIEW",
        "Classified outflow exceeds inflow",
        "No new loan is recommended automatically.",
    ),
    (
        "personal_data_gap",
        "PERSONAL",
        "WAITING_FOR_USER",
        "Incoming credit is not classified",
        "User confirmation is required before treatment changes.",
    ),
    (
        "guardian_invoice_arithmetic",
        "GUARDIAN",
        "ACTION_READY",
        "Invoice line arithmetic does not reconcile",
        "Structured values are user-submitted; document remains unscanned.",
    ),
    (
        "guardian_low_confidence",
        "GUARDIAN",
        "IN_REVIEW",
        "Evidence quality is too weak for a conclusion",
        "The workflow must abstain until a human verifies the source.",
    ),
    (
        "opportunity_net_income",
        "OPPORTUNITY",
        "OPEN",
        "A paid task needs travel and materials costs",
        "Gross pay is not net income.",
    ),
    (
        "opportunity_unverified_client",
        "OPPORTUNITY",
        "WAITING_FOR_USER",
        "Client identity and payment terms are missing",
        "No application or data sharing occurs without approval.",
    ),
    (
        "entitlement_stale_source",
        "ENTITLEMENT",
        "IN_REVIEW",
        "Scheme source is older than the allowed freshness window",
        "No eligibility or award is asserted.",
    ),
    (
        "entitlement_missing_proof",
        "ENTITLEMENT",
        "WAITING_FOR_USER",
        "Potential benefit match needs enrollment proof",
        "Potential match is not a confirmed entitlement.",
    ),
    (
        "crisis_salary_delay",
        "CRISIS",
        "ACTION_READY",
        "Income delay creates an essentials shortfall",
        "Reversible essentials-first replanning; no automatic debt push.",
    ),
    (
        "crisis_medical_shock",
        "CRISIS",
        "WAITING_EXTERNAL",
        "Medical cost requires provider clarification",
        "No payment or claim is submitted.",
    ),
    (
        "enterprise_below_cost_quote",
        "ENTERPRISE",
        "IN_REVIEW",
        "Draft quote falls below full unit cost",
        "Quote is not sent and no order is created.",
    ),
    (
        "enterprise_profitable_quote",
        "ENTERPRISE",
        "RESOLVED",
        "A user-reviewed price covers listed unit costs",
        "Resolved is a workflow state, not a settled payment.",
    ),
    (
        "commons_low_quorum",
        "PERSONAL",
        "OPEN",
        "A collective demand cohort is below threshold",
        "No private household records are shared.",
    ),
    (
        "commons_differencing_guard",
        "PERSONAL",
        "CLOSED",
        "Repeated aggregate query would reveal a small cohort",
        "The query is suppressed; minimum cohort is not a DP guarantee.",
    ),
    (
        "consent_revoked_mid_mission",
        "PERSONAL",
        "CLOSED",
        "Purpose consent was revoked before a task step",
        "Future protected reads/actions are blocked.",
    ),
    (
        "mission_worker_recovery",
        "PERSONAL",
        "WAITING_EXTERNAL",
        "Worker resumes after the last durable checkpoint",
        "No blind replay when provider state is uncertain.",
    ),
    (
        "case_stale_version",
        "PERSONAL",
        "IN_REVIEW",
        "Two edits race with the same prior version",
        "One write wins; the stale caller must reload.",
    ),
]


def main() -> None:
    rng = random.Random(SEED)
    base = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
    cases: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    scenarios: list[dict[str, object]] = []
    transition_paths = {
        "OPEN": ["OPEN"],
        "IN_REVIEW": ["OPEN", "IN_REVIEW"],
        "ACTION_READY": ["OPEN", "IN_REVIEW", "ACTION_READY"],
        "WAITING_FOR_USER": ["OPEN", "IN_REVIEW", "WAITING_FOR_USER"],
        "WAITING_EXTERNAL": ["OPEN", "IN_REVIEW", "ACTION_READY", "WAITING_EXTERNAL"],
        "RESOLVED": ["OPEN", "IN_REVIEW", "ACTION_READY", "WAITING_EXTERNAL", "RESOLVED"],
        "CLOSED": ["OPEN", "CLOSED"],
    }
    for index in range(1, 73):
        scenario = SCENARIOS[(index - 1) % len(SCENARIOS)]
        slug, engine, status, title, safety_note = scenario
        case_id = f"SYN-CASE-{index:04d}"
        target_status = status if index <= len(SCENARIOS) else rng.choice(STATUSES)
        path = transition_paths[target_status]
        owner = f"SYN-USER-{rng.randint(1, 24):03d}"
        created_at = base - timedelta(days=rng.randint(0, 45), hours=rng.randint(0, 18))
        currency = "INR"
        amount_minor = rng.choice([None, 49900, 64900, 125000, 240000, 1850000])
        synthetic_case = {
            "case_id": case_id,
            "owner_ref": owner,
            "source_engine": engine,
            "scenario": slug,
            "title": title,
            "status": target_status,
            "state_version": len(path),
            "currency": currency,
            "amount_minor": amount_minor,
            "environment": "SYNTHETIC",
            "synthetic_only": True,
            "backend_api_coverage": (
                "WORKFLOW_API_CONTRACT_AVAILABLE; fixture is not an API-created case"
                if engine == "PERSONAL"
                else "FIXTURE_PREVIEW_ONLY"
            ),
            "safety_note": safety_note,
            "external_actions_taken": False,
            "verified_value_created_minor": 0,
        }
        cases.append(synthetic_case)
        prior = None
        elapsed_minutes = 0
        for sequence, state in enumerate(path, start=1):
            if sequence > 1:
                elapsed_minutes += rng.randint(3, 40)
            occurred = created_at + timedelta(minutes=elapsed_minutes)
            event = {
                "event_id": f"{case_id}-EV-{sequence:02d}",
                "case_id": case_id,
                "owner_ref": owner,
                "event_sequence": sequence,
                "event_type": "CASE_OPENED" if sequence == 1 else "STATUS_CHANGED",
                "from_status": prior,
                "to_status": state,
                "created_at": occurred.isoformat(),
                "actor_ref": owner,
                "idempotency_key": f"{case_id}-IDEM-{sequence:02d}",
                "environment": "SYNTHETIC",
                "immutable": True,
            }
            events.append(event)
            prior = state
        scenarios.append(
            {
                "scenario_id": f"CASEBOOK-{index:03d}",
                "case_id": case_id,
                "scenario": slug,
                "engine": engine,
                "target_status": target_status,
                "expected_invariants": [
                    "owner_scope_is_enforced",
                    "state_version_matches_event_sequence",
                    "event_history_is_append_only",
                    "verified_value_remains_zero_without_settlement_evidence",
                    "no_external_action_occurs_without_an_approved_adapter",
                ],
                "safety_note": safety_note,
                "synthetic_only": True,
            }
        )

    (ROOT / "cases.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True) + "\n" for x in cases), encoding="utf-8"
    )
    (ROOT / "events.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True) + "\n" for x in events), encoding="utf-8"
    )
    (ROOT / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "dataset": "AwnNORA Personal Casebook Synthetic Lifecycle v1",
        "seed": SEED,
        "generated_at": "fixed-seed reproducible corpus; timestamps are synthetic",
        "case_count": len(cases),
        "event_count": len(events),
        "scenario_count": len(scenarios),
        "owners": 24,
        "engines": ENGINES,
        "status_distribution": {
            status: sum(x["status"] == status for x in cases) for status in STATUSES
        },
        "backend_scope": (
            "Only PERSONAL lifecycle is implemented by the Iteration 06 casebook API. "
            "Other engine labels are scenario fixtures, not implemented backends."
        ),
        "money_rule": (
            "amount_minor is integer paise; all verified_value_created_minor values are zero "
            "because no real settlement evidence exists."
        ),
        "privacy_rule": (
            "No real people, account numbers, bank identifiers, phone numbers "
            "or credentials are present."
        ),
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
