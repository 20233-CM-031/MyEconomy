#!/usr/bin/env python3
"""Validate reproducibility, event ordering and synthetic-value safety rules."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    cases = read_jsonl(ROOT / "cases.jsonl")
    events = read_jsonl(ROOT / "events.jsonl")
    scenarios = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    events_by_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    event_ids: set[str] = set()
    for event in events:
        events_by_case[str(event["case_id"])].append(event)
        assert event["environment"] == "SYNTHETIC"
        assert event["immutable"] is True
        assert event["event_id"] not in event_ids
        event_ids.add(str(event["event_id"]))

    allowed = {
        "OPEN": {"IN_REVIEW", "CLOSED"},
        "IN_REVIEW": {"ACTION_READY", "WAITING_FOR_USER", "CLOSED"},
        "ACTION_READY": {"IN_REVIEW", "WAITING_FOR_USER", "WAITING_EXTERNAL", "CLOSED"},
        "WAITING_FOR_USER": {"IN_REVIEW", "ACTION_READY", "CLOSED"},
        "WAITING_EXTERNAL": {"IN_REVIEW", "RESOLVED", "CLOSED"},
        "RESOLVED": {"CLOSED"},
        "CLOSED": set(),
    }
    case_ids: set[str] = set()
    cases_by_id: dict[str, dict[str, object]] = {}
    for case in cases:
        case_id = str(case["case_id"])
        assert case_id not in case_ids
        case_ids.add(case_id)
        cases_by_id[case_id] = case
        timeline = sorted(events_by_case[case_id], key=lambda x: int(x["event_sequence"]))
        assert timeline, f"{case_id} has no timeline"
        assert [int(x["event_sequence"]) for x in timeline] == list(range(1, len(timeline) + 1))
        first = timeline[0]
        assert first["event_type"] == "CASE_OPENED"
        assert first["from_status"] is None and first["to_status"] == "OPEN"
        prior_status = "OPEN"
        prior_time = datetime.fromisoformat(str(first["created_at"]))
        for event in timeline[1:]:
            assert event["event_type"] == "STATUS_CHANGED"
            assert event["from_status"] == prior_status
            assert event["to_status"] in allowed[prior_status]
            event_time = datetime.fromisoformat(str(event["created_at"]))
            assert event_time >= prior_time
            prior_status = str(event["to_status"])
            prior_time = event_time
        assert prior_status == case["status"]
        assert int(case["state_version"]) == len(timeline)
        assert all(item["owner_ref"] == case["owner_ref"] for item in timeline)
        assert all(item["actor_ref"] == case["owner_ref"] for item in timeline)
        assert case["synthetic_only"] is True and case["environment"] == "SYNTHETIC"
        assert case["external_actions_taken"] is False
        assert int(case["verified_value_created_minor"]) == 0
        amount = case["amount_minor"]
        assert amount is None or (isinstance(amount, int) and amount >= 0)
        assert case["currency"] == "INR"
    assert set(events_by_case) == case_ids
    assert len({str(case["owner_ref"]) for case in cases}) == manifest["owners"]
    assert len(cases) == manifest["case_count"] == len(scenarios)
    assert len(events) == manifest["event_count"]
    assert all(scenario["synthetic_only"] is True for scenario in scenarios)
    assert {str(x["case_id"]) for x in scenarios} == case_ids
    assert all(
        scenario["target_status"] == cases_by_id[str(scenario["case_id"])]["status"]
        for scenario in scenarios
    )
    actual_engines = {str(case["source_engine"]) for case in cases}
    assert actual_engines == set(manifest["engines"])
    status_distribution = {
        status: sum(case["status"] == status for case in cases) for status in sorted(allowed)
    }
    assert status_distribution == manifest["status_distribution"]
    print(
        f"PASS: {len(cases)} synthetic cases, {len(events)} immutable/legal events, "
        f"{len(scenarios)} scenarios"
    )


if __name__ == "__main__":
    main()
