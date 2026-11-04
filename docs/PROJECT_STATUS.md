# AwnNORA Project Status

**Last reconciled:** 2026-11-04
**Product/project:** AwnNORA
**Implementation repository:** `20233-CM-031/MyEconomy`
**Default branch:** `main`
**Verified remote `main` HEAD:** `a55cb388ef7baf72766e2fcabe89f0dee1c45979` — merge of PR #2, `iteration/02-financial-data-plane`
**Current local candidate:** Iteration 03 — Economic Intelligence Domain Kernel
**Remote Iteration 03 branch/PR:** Not created; GitHub branch write is blocked by app-installation ownership mismatch.

## 1. Identity and architecture

AwnNORA is the confirmed product/project name. `MyEconomy` remains the existing code repository and Python package name, not an alternative brand. **MAKOS** is the operational workspace and workflow surface. **GENIEA** coordinates personal/specialist agents, bounded missions and tool use. **KRN** maintains knowledge, evidence, relationships, provenance and temporal state. These are logical systems; the repository does not yet contain complete MAKOS, GENIEA or KRN runtime packages. Read `AWNNORA_CONTEXT_MAP.md` before further engineering.

## 2. Verified remote baseline

Live GitHub read confirms `main` at `a55cb388ef7baf72766e2fcabe89f0dee1c45979`, merging PR #2 (`feat: add owner-scoped financial data plane`). The prior Iteration 02 CI run `41801123405` passed the Python 3.12, Python 3.13 and PostgreSQL 16 jobs. Iteration 00, 01 and 02 are therefore the remote baseline. Some earlier status text in the repository was stale and described the pre-PR #2 SHA; this status replaces it.

The current local worktree was reconstructed from `MyEconomy_Iteration_02_Complete_Project.zip` and reconciled with live repository metadata and memory docs. It is not a remote `git clone` and must be applied to a fresh owner-authenticated checkout by branch/patch before merging.

## 3. Implemented and merged

### Iteration 00 — deterministic cashflow foundation

- Python 3.12/3.13 FastAPI application, Pydantic API contracts and health/readiness.
- Framework-independent Decimal money/cashflow analysis over caller-provided inputs.

### Iteration 01 — identity, household trust and consent

- Registration, email verification, opaque session lifecycle and password hashing.
- Household ownership, membership and invitation lifecycle.
- Purpose/category/recipient-scoped consent and revocation.
- Append-only audit events protected at ORM/database layers.

### Iteration 02 — owner-scoped Financial Data Plane v1

- Financial account metadata, transaction import batches, persisted ledger and recurring obligations.
- Bounded strict CSV parsing, source SHA-256, sanitized filename, owner-scoped idempotency, provenance and duplicate review signals.
- Integer minor-unit money and currency/account constraints; no implicit FX.
- Monotonic provider status transitions and financial-fact immutability enforced in application/database logic.
- Posted-only cashflow read model with conservative `IGNORE` default for unclassified CSV rows.
- Synthetic seeder guarded for development/test/demo only.

## 4. Iteration 03 — local domain kernel (not remotely pushed)

Added `src/myeconomy/domain/economic_intelligence.py` and `tests/test_economic_intelligence.py`. The module provides:

1. Guardian invoice arithmetic/evidence/confidence review, with `CONSISTENT`, `REVIEW_REQUIRED` and `ABSTAIN` outcomes; it does not assert fraud.
2. Offer evaluation using baseline cost, provider price, sponsor credit, additional spend, fees and switching cost; rejects non-positive value and incompatible/uncertain offers.
3. Consent-aware Commons aggregation with event-time consent, revocation/expiry checks, freshness and minimum cohort suppression. Cohort size alone is not a formal privacy guarantee.
4. VIVC accounting that counts only live, verified, evidence-verified and settlement-verified events.
5. GENIEA bounded mission transition and tool-authorization primitives requiring active permission and, for external mutations, explicit approval plus idempotency.

This is a **domain kernel**, not an end-to-end feature. It has no authenticated HTTP routes, document vault, OCR/model extraction gateway, database persistence, Guardian case lifecycle, durable GENIEA runtime/checkpoints, KRN graph persistence, Commons marketplace, settlement/payout or MAKOS user interface.

## 5. Local verification

- `python -m pytest -q`: **79 passed** (56 existing + 23 new focused tests).
- `python -m compileall -q src tests migrations scripts`: passed.
- `PYTHONPATH=src python -m alembic upgrade head`: passed.
- `PYTHONPATH=src python -m alembic downgrade base`: passed.
- `PYTHONPATH=src python -m alembic upgrade head` after downgrade: passed.
- `python demo_data/synthetic_v1/validate_dataset.py`: passed all independent checks across 42 tables and 17,425 synthetic rows, including cross-table constraints, privacy-safe Commons fixtures, value labels, multimodal file hashes, export parity and SQLite integrity.
- Ruff is unavailable in the isolated environment; Ruff lint/format are **unverified** and must run in CI.
- No migration changed in Iteration 03; live PostgreSQL migration service test was not rerun for this pure domain slice.

## 6. GitHub write blocker

Authenticated GitHub login: `20233-CM-031`. The only GitHub App installation currently visible is installation `118719658` under account `kareem1207`; its repository list shows `kareem1207/Aura`, not `20233-CM-031/MyEconomy`. The repository metadata shows the user's admin/push permission, but connector branch creation returned HTTP 403 `Resource not accessible by integration`. No remote branch, commit or PR exists for Iteration 03.

Resolution: install/re-authorize the GitHub App on owner account `20233-CM-031` and grant this repository Contents write, Git References write and Pull Requests write. Do not paste personal access tokens into chat. After the connection is fixed, re-read `main` and create `iteration/03-guardian-evidence-kernel` from the current SHA; never write directly to `main`.

## 7. Next engineering slice

Build a real Guardian evidence workflow end-to-end: owner-scoped document intake and validation -> content hash and safe storage -> Meta model extraction into a typed schema with evidence locators/confidence -> deterministic invoice review -> persisted Guardian case/findings -> human-approved draft action -> auditable outcome. Add durable GENIEA mission/checkpoint persistence and KRN evidence/relationship interfaces only as required by this vertical slice. Expose the case timeline and approval state through MAKOS. Keep synthetic/demo and live adapters fenced.

## 8. Status rule

Current code/tests/migrations and live GitHub state determine what works. Keep `AWNNORA_CONTEXT_MAP.md`, `PROJECT_MEMORY.md`, this file, `CODEBASE_MAP.md`, `FEATURE_CATALOG.md` and each iteration record synchronized. Never describe local work as pushed; never call a design or fixture a live integration.
