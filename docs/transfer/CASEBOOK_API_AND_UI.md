# Casebook API and MAKOS integration notes

The Personal Casebook is the first reusable action spine. It binds a current Personal Power finding to an owner-scoped case and an immutable sequence of user-workflow events.

## Create

```http
POST /api/v1/cases/from-finding
Authorization: Bearer <verified-user-session>
Idempotency-Key: makos-case-open:<unique-key>
Content-Type: application/json

{
  "finding_id": "DUP-001",
  "period_start": "2026-10-01",
  "period_end": "2026-10-31",
  "as_of": "2026-11-04",
  "currency": "INR",
  "obligation_horizon_days": 30
}
```

The server rebuilds the report from persisted owner records. It does not trust a client-supplied amount, title, finding explanation or evidence reference. If a finding is no longer current for that same reporting window, the API returns not-found and asks the client to refresh.

## Transition

```http
POST /api/v1/cases/<case-id>/transition
Authorization: Bearer <verified-user-session>
Idempotency-Key: makos-case-transition:<unique-key>
Content-Type: application/json

{
  "to_status": "IN_REVIEW",
  "expected_version": 1,
  "note": "I checked the original statement."
}
```

The API returns `409` on a stale version or a conflicting idempotency payload. Event sequence equals `state_version`. The client should reload after a stale write and present the current authoritative history. Minor-unit amounts are returned as integer strings (for example `"64900"` paise) to preserve BIGINT precision in JavaScript clients.

## UI truth

- Synthetic mode stores casebook examples in local browser state and labels them synthetic.
- Live mode calls the authenticated casebook API.
- Case status describes user workflow only. No provider communication or payment is executed.
- `RESOLVED` does not imply a refund or savings; the VIVC field remains controlled by a distinct evidence and settlement process.
- Database triggers validate every event insert against the case owner, current version, current status and event shape; event rows are append-only.
- Source facts cannot be edited, and ordinary case deletion is blocked so a cascading delete cannot silently remove the event history. A future approved retention/erasure workflow must explicitly handle this boundary.
- Other engine labels in the lifecycle dataset are fixture previews, not live case adapters.
