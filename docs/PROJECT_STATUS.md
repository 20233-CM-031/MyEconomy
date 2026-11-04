# AwnNORA Project Status

**Last reconciled:** 2026-11-04
**Product/project:** AwnNORA
**Implementation repository:** `20233-CM-031/MyEconomy`
**Default branch:** `main`
**Verified remote `main` HEAD:** `f2eee774a6915ccea98e0353494704b81635b183` — read-only inspected after the owner uploaded the previous MAKOS/Meta delivery.
**Latest merged engineering iteration:** Iteration 05 — Personal Mode Power Report + first-user journey + Scenario Lab.
**Next local overlay:** Iteration 06 Personal Casebook package; not yet applied by this assistant.

## 1. Product identity and architecture

AwnNORA is the confirmed project/product name. `MyEconomy` is the implementation repository and Python package name. **MAKOS** is the operational workspace and workflow surface; **GENIEA** coordinates bounded agent missions and tools; **KRN** structures private knowledge, evidence, provenance and relationships. These are first-class architecture responsibilities, not claims that all three runtime subsystems already exist. Read `docs/AWNNORA_CONTEXT_MAP.md` first.

AwnNORA must deliver individual value on Day One through Personal Mode. Commons multiplies value through explicit, purpose-limited, revocable sharing; it must never be a prerequisite for a person to use the product. The product is not merely a budget tracker, ad platform or chatbot.

## 2. Verified remote baseline

Read-only GitHub inspection on 2026-11-04 confirmed:

- Repository: `20233-CM-031/MyEconomy`; default branch `main`.
- Current `main` HEAD at Iteration 06 preparation: `f2eee774a6915ccea98e0353494704b81635b183`; read-only repository tree and key source files were inspected.
- PR #4 (Guardian evidence/case workflow) and PR #5 (Personal Power Report / Scenario Lab) are merged.
- PR #5 reports 94 passing tests, one warning, and Ruff lint/format checks passing. The available GitHub status/workflow endpoints returned no status records for the merge SHA, so this report does not independently certify a green CI run.
- No branch, commit, PR or file was written by this assistant. All subsequent implementation is delivered as local downloadable packages for the repository owner to apply.

## 3. Iteration delivery ledger

### Iteration 00 — deterministic cashflow foundation (merged)

- FastAPI/Pydantic application and health/readiness routes.
- Framework-independent Decimal money/cashflow calculation with currency precision rules.

### Iteration 01 — identity, household trust and consent (merged)

- Registration, email verification, opaque sessions, household membership/invitations, consent grants/revocation and append-only audit events.
- Password hashing, hashed session/verification token storage, verified-email gates and ownership boundaries.

### Iteration 02 — financial data plane v1 (merged)

- Owner-scoped financial accounts, bounded CSV ingestion, import provenance/idempotency, persisted transactions and recurring obligations.
- Integer minor-unit amounts with currency, immutable financial facts and monotonic provider status transitions guarded at application/database layers.
- Persisted posted-only cashflow read model. Unknown transaction classification defaults to `IGNORE`; no inferred income/expense.
- Existing synthetic relational corpus: 42 entity tables, 17,425 rows, 120 fictional adults, 55 households and multimodal documents.

### Iteration 03 — economic-intelligence domain kernel (merged in PR #3)

- Deterministic invoice arithmetic/evidence review and confidence-based abstention.
- Full-cost offer optimizer, consent-aware Commons aggregation primitives, strict VIVC accounting and GENIEA mission/tool policy primitives.
- `domain/economic_intelligence.py` and its focused tests exist on remote `main`.
- These are domain rules; they do not by themselves implement a persistent Commons marketplace, durable GENIEA runtime, Meta gateway or MAKOS UI.

### Iteration 04 — Guardian evidence and invoice-review workflow (local candidate)

The local source worktree contains a complete first authenticated API vertical slice:

- Verified-user-only upload of PDF/PNG/JPEG with bounded 5 MiB streaming body, signature checks, sanitized display filename, SHA-256, owner-scoped idempotency and private local filesystem storage.
- Persisted evidence metadata and invoice-review cases with owner-scoped composite foreign key, review request hash/idempotency, structured invoice snapshot, findings, source hash and append-only audit events.
- Deterministic review against exact monetary arithmetic and the same user's prior invoices.
- Owner-scoped case list/detail and evidence metadata/download routes.
- Deterministic clarification draft, followed by an explicit user confirmation state. Approval records that the user may send it; **no provider message is sent**.
- Three fictional Guardian PDF documents plus structured fixture payloads and an API demo runner.

**Important boundaries:** files remain `STORED_UNSCANNED`; this iteration does not malware-scan, OCR, parse PDF/image bytes, invoke a Meta model, validate the supplied locators against document text, or contact a provider. The structured invoice fields and confidence are user-submitted demo data. The filesystem adapter is for local/demo only, not production encrypted storage.

## 4. Current local verification evidence

Commands/results for the Iteration 04 candidate as of 2026-11-04:

- `PYTHONPATH=src pytest -q`: **84 passed**.
- `python -m compileall -q src tests migrations scripts demo_data/synthetic_v1`: passed.
- SQLite migration lifecycle: `alembic upgrade head` → `alembic downgrade base` → `alembic upgrade head`: passed; current revision `c1d4e7a9f204`.
- `PYTHONPATH=src python demo_data/synthetic_v1/validate_dataset.py`: passed all independent relational, export, privacy-fixture and SQLite integrity checks for 42 tables / 17,425 rows.
- Guardian PDF text was inspected with `pdftotext -layout`; fixture page/line/column locators were aligned to the generated PDFs and their SHA-256 hashes are recorded in `metadata/guardian_workflow_manifest.json`.
- Python 3.13 local runtime was used. Python 3.12 was not available locally.
- Ruff was not available locally; lint/format remain unverified.
- A live PostgreSQL 16 migration/service test for the new Guardian migration has not been run. SQLite migration lifecycle success must not be described as PostgreSQL verification.
- The HTTP workflow is covered by `tests/test_guardian_workflow.py`; the standalone demo runner is syntax-compiled but has not been run against a separately started server with a real login session in this environment.

## 5. Guardian API surface added locally in Iteration 04

- `POST /api/v1/guardian/evidence-documents` — upload PDF/PNG/JPEG bytes, `Idempotency-Key`, `X-Filename`.
- `GET /api/v1/guardian/evidence-documents` — list own evidence metadata.
- `GET /api/v1/guardian/evidence-documents/{document_id}/download` — owner-scoped original file download.
- `POST /api/v1/guardian/invoice-reviews` — submit structured invoice fields and evidence locators for deterministic review.
- `GET /api/v1/guardian/cases` and `GET /api/v1/guardian/cases/{case_id}` — owner-scoped cases.
- `POST /api/v1/guardian/cases/{case_id}/draft` — create deterministic clarification draft.
- `POST /api/v1/guardian/cases/{case_id}/approve-draft` — explicit approval for the user to send manually; no external side effect.

All routes require verified authentication. Document and case metadata are scoped to the current user. No household membership shortcut exists.

## 6. Next production-readiness gates

1. Replace local file adapter with encrypted object storage, KMS-managed encryption, virus/malware scanning, quarantine state, safe content inspection, retention and erasure controls.
2. Add a typed Meta model gateway for OCR/multimodal extraction; output must include model/prompt/schema versions, exact evidence locators and confidence, then pass deterministic checks. Evaluate field exact-match, citation correctness and abstention on synthetic fixtures.
3. Validate page/region evidence locators against the source document before presenting them as verified evidence.
4. Add persistent GENIEA missions, step leases, checkpoints, outbox/idempotent tool execution, retry/reconciliation and approval records.
5. Build MAKOS Personal Mode UI for upload, evidence review, case timeline, draft preview and user approval.
6. Implement KRN typed private graph partitions, temporal/provenance relationships and explicit sharing edges.
7. Add persistent Commons demand and offers, anti-differencing controls, privacy risk analysis, fairness and auditable settlement. Cohort threshold alone is not formal differential privacy.
8. Add concurrency, retention, malware, object-store failure, backup/restore and PostgreSQL 16 integration tests; add observability and operational runbooks.
9. Add live provider integrations only after contract, credentials, lawful purpose, user authority, idempotency and reconciliation contracts exist. Never imply a fixture adapter is a live partner.
10. Build remaining Opportunity/Benefits, Resource Exchange, Crisis Shield, Economic Defence and One-Person Enterprise verticals as complete end-to-end slices rather than disconnected stubs.

## 7. Source-of-truth rule

The live GitHub code/migrations/tests and remote branch state determine what is merged. This file records current local candidate facts separately. A local archive, a generated overlay or a passing local test suite is never called pushed/merged. Update this file, the context map, project memory, codebase map, feature catalog and iteration report in the same engineering change.


<!-- AWNNORA-TRANSFER-ITERATION-05 -->
## Local transfer overlay — 2026-11-04

The verified remote baseline used to prepare the additive overlay was `60fa93d191fcd6566719db553d4628905a0b64f7`. The overlay adds a local Personal Mode Power Report vertical slice and a first-user runner. These additions are **not merged or pushed** by the assistant; after the repository owner applies them, run the full repository suite and the first-user runbook before treating the slice as accepted. Package-level domain tests and scenario-lab validation are recorded in `docs/transfer/ITERATION-05-PERSONAL-POWER.md`.

The Scenario Lab ships 46 templates × 25 deterministic replicas (1,150 runs) across 12 capability categories. All generated runs are `SYNTHETIC_FIXTURE`; no external side effect occurs and VIVC is zero. This complements—not replaces—the existing 42-table / 17,425-row `synthetic_v1` corpus.


<!-- AWNNORA-TURBO-WEB-META-2026-11-04 -->
## 8. Next overlay — MAKOS web + Meta assistance

A local additive package supplies a TypeScript/React/Vite MAKOS workspace and an API-backed Muse Spark 1.3 Standard-mode explanation path with `AI_ASSISTANCE` consent. It is not included in the verified remote HEAD until applied by the repository owner. The Meta endpoint sends aggregate Personal Power fields and genericized findings only; it does not receive transaction rows, account identifiers, names, payee labels, documents or evidence locators. Run `docs/transfer/TURBO_WEB_META_RUNBOOK.md` and the transfer validation steps before accepting the slice.

## Iteration 07 — Personal Economic Casebook & Workflow Workspace

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
