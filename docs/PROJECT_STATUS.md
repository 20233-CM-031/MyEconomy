# AwnNORA Project Status

**Last reconciled:** 2026-11-04
**Product/project:** AwnNORA
**Implementation repository:** `20233-CM-031/MyEconomy`
**Default branch:** `main`
**Verified remote `main` HEAD:** `7408269421f4c1a166e58ec0310fc9c9da2c2ede` — merge of PR #5, `iteration/05-personal-power-scenario-lab`
**Latest merged engineering iteration:** Iteration 05 — Personal Mode Power Report + first-user journey + Scenario Lab.
**Next local overlay:** MAKOS TypeScript web application + consent-gated Meta model explanation adapter; this package is not yet applied or pushed.

## 1. Product identity and architecture

AwnNORA is the confirmed project/product name. `MyEconomy` is the implementation repository and Python package name. **MAKOS** is the operational workspace and workflow surface; **GENIEA** coordinates bounded agent missions and tools; **KRN** structures private knowledge, evidence, provenance and relationships. These are first-class architecture responsibilities, not claims that all three runtime subsystems already exist. Read `docs/AWNNORA_CONTEXT_MAP.md` first.

AwnNORA must deliver individual value on Day One through Personal Mode. Commons multiplies value through explicit, purpose-limited, revocable sharing; it must never be a prerequisite for a person to use the product. The product is not merely a budget tracker, ad platform or chatbot.

## 2. Verified remote baseline

Read-only GitHub inspection on 2026-11-04 confirmed:

- Repository: `20233-CM-031/MyEconomy`; default branch `main`.
- Current `main` HEAD: `7408269421f4c1a166e58ec0310fc9c9da2c2ede`, merge of PR #5 (`feat: add AwnNORA Personal Mode first-user journey and Scenario Lab`).
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
