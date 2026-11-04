# Iteration 06 — Personal Economic Casebook

## Product outcome

A Personal Power finding can become a durable user-owned work item. The case freezes the server-computed finding and reporting window, then moves through an explicit state machine with an append-only timeline. MAKOS is the human-facing case workspace; the API is the source of truth.

## Included in this delivery

- Owner-verified `POST /api/v1/cases/from-finding`, backed by the current persisted Personal Power report. The request accepts a finding reference and report window only. Title, amount, explanation and evidence references are recomputed on the server.
- Owner-scoped `GET /api/v1/cases` and `GET /api/v1/cases/{id}`.
- `POST /api/v1/cases/{id}/transition` with `expected_version` and `Idempotency-Key`.
- A deterministic state machine, optimistic compare-and-set, retry/replay checks, case source snapshot, immutable event records and audit events. Minor-unit amounts are serialized as decimal integer strings so browser number parsing cannot silently lose BIGINT precision.
- MAKOS Casebook screen and Open Case action from Power Report findings.
- 72 reproducible synthetic lifecycle cases, 198 events and 72 scenario checks spanning the intended engines. Non-Personal entries are fixture previews only.

## State contract

`OPEN → IN_REVIEW → ACTION_READY → WAITING_FOR_USER / WAITING_EXTERNAL → RESOLVED → CLOSED`, with the narrower alternatives enforced in `domain/casebook.py`. `CLOSED` is terminal. Every transition increments `state_version` exactly once and appends one event with the same sequence number. An event cannot be updated or deleted through the ORM or supported database triggers. The database also rejects inserted timeline events that do not match the case owner, current version, current status and event type.

`WAITING_EXTERNAL` means the user is tracking a separately performed external step. The application itself does not send messages, make payments, file claims, cancel subscriptions or call a provider. `RESOLVED` means the user marked the workflow resolved. It is not proof of settlement and never changes VIVC.

## Trust and failure controls

- All API operations require verified authentication.
- All case and event reads use the authenticated owner scope.
- Client-provided narrative, title, monetary amount and source evidence are rejected as extra create fields.
- Case creation has both request-key idempotency and a natural uniqueness key on owner + finding + reporting window + currency.
- Transition retries replay only when the same case event key and exact request hash match. Reusing the key for a changed payload conflicts.
- Stale state versions return conflict; clients must refresh before retrying. Overlapping retries with the same key are rechecked after compare-and-set failure so a committed winner can be returned as a replay. Case deletion is blocked at ORM and database levels; data-retention erasure requires a separate approved workflow.
- The timeline records no credentials, source CSV rows, document bytes or private bank identifiers.
- `source_snapshot.value_status` stays at the finding's non-outcome state. No synthetic or prospective value is counted as verified.

## API

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/v1/cases/from-finding` | Open a case from a currently present Personal Power finding |
| GET | `/api/v1/cases?limit=50` | List the current user's cases |
| GET | `/api/v1/cases/{case_id}` | Read case and event timeline |
| POST | `/api/v1/cases/{case_id}/transition` | Move case with version precondition and idempotency key |

## Validation

Run the domain and API tests with `pytest tests/test_casebook_domain.py tests/test_personal_casebook_api.py`. Run `python demo_data/casebook_v1/validate_casebook_dataset.py`. Run the complete repository test suite and Alembic upgrade/downgrade lifecycle before deployment. This package's validation report states exactly which checks were executed in the build environment.

## Not implemented by this iteration

Persistent Guardian/Opportunity/Entitlement/Crisis/Enterprise/Commons case adapters; document scanning or OCR; GENIEA durable execution; KRN persistence; notifications; provider dispatch; payments or settlement; benefits verification; payout ledger; external case escalation; account export/deletion. Do not market these as working features on the basis of the synthetic scenarios.
