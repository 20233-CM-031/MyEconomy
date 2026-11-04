# Iteration 03 — AwnNORA Economic Intelligence Domain Kernel

**Date:** 2026-11-04
**Status:** Merged into remote `main` through PR #3; merge commit `5b5cf669773d5c0cd33f5abffb8c46d44cead797`. The merged commit is verified by live GitHub read; no CI result was returned by the available status endpoints.
**Base reference:** Iteration 02 merged `main` at `a55cb388ef7baf72766e2fcabe89f0dee1c45979`; merged by PR #3.
**Implementation package:** `myeconomy.domain.economic_intelligence`.

## 1. Goal

Establish the deterministic policy and economic rules needed before adding model gateways, Guardian APIs, Commons services or a durable GENIEA runtime. The code must keep arithmetic, consent eligibility, net-value calculations, verified-outcome accounting and tool authorization outside the LLM.

## 2. Implemented domain kernel

### Guardian invoice review

- Validates SHA-256 source identity and field-level evidence references.
- Checks monetary precision against the existing currency registry.
- Checks line-item arithmetic, subtotal and total equations, issue/due date order, evidence completeness and confidence thresholds.
- Flags exact duplicate document hashes and large comparable provider price increases.
- Returns `CONSISTENT`, `REVIEW_REQUIRED` or `ABSTAIN`; it does not call an invoice fraudulent or claim a legal violation.

### Offer net-value evaluation

- Calculates baseline total cost versus proposed provider price, sponsor credit, one-time and recurring fees, extra spend and switching costs.
- Requires confirmed eligibility, compatible quality and user constraints.
- Rejects non-positive net benefit rather than ranking by headline discount.
- Uses integer minor units and one currency per comparison.

### Commons consent-aware aggregation

- Checks event-time consent, current revocation/expiry, timezone awareness and signal freshness.
- Deduplicates one contribution per person/cohort/category/environment.
- Suppresses cohorts below the configured minimum and returns aggregate counts/values rather than member records.
- Cohort thresholds alone are not a formal privacy guarantee; production requires anti-differencing, abuse controls and a privacy analysis (and potentially differential privacy).

### VIVC accounting

- Counts only LIVE, VERIFIED, evidence-verified and settlement-verified events.
- Excludes estimates, synthetic/sandbox records and unverified attempts.
- Rejects duplicate idempotency keys and mixed currencies.

### GENIEA mission/tool policy primitives

- Defines bounded mission state transitions, including approval waiting and terminal states.
- Requires active permission scope for tool execution.
- Requires explicit approval and an idempotency key before externally mutating actions.
- Fails closed when execution environment and adapter environment do not match.

## 3. Files changed in the local worktree

| Path | Change | Purpose |
|---|---|---|
| `src/myeconomy/domain/economic_intelligence.py` | Added | Framework-independent economic rules and policy primitives |
| `tests/test_economic_intelligence.py` | Added | 23 tests for normal, boundary, rejection and privacy/authorization paths |
| `docs/AWNNORA_CONTEXT_MAP.md` | Added | Canonical product/architecture/codebase context map |
| `docs/iterations/ITERATION-03.md` | Added | This implementation record |
| `docs/iterations/ITERATION-03-FILE-MANIFEST.md` | Added | File-level handoff manifest |
| `README.md` | Updated | AwnNORA identity and iteration state |
| `AGENTS.md` | Updated | Corrected product and system naming instructions |
| `docs/PROJECT_MEMORY.md` | Updated | Reconciled confirmed brand and architecture references |
| `docs/PROJECT_STATUS.md` | Updated | Actual remote base and local Iteration 03 state |
| `docs/ARCHITECTURE.md` | Updated | MAKOS/GENIEA/KRN relationship and implementation boundaries |
| `docs/CODEBASE_MAP.md` | Updated | Added real location/scope of the new domain kernel |
| `docs/FEATURE_CATALOG.md` | Updated | Marks domain primitives as partial, not complete services |
| `docs/AI_COLLABORATION_PROTOCOL.md` | Updated | Corrected project identity |
| `docs/PRODUCT_VISION.md` | Updated | Corrected product identity |

## 4. Verification

- `python -m pytest -q`: **79 passed** (56 existing + 23 new).
- `python -m compileall -q src tests migrations scripts`: passed.
- `PYTHONPATH=src python -m alembic upgrade head`: passed.
- `PYTHONPATH=src python -m alembic downgrade base`: passed.
- `PYTHONPATH=src python -m alembic upgrade head` after downgrade: passed.
- `python demo_data/synthetic_v1/validate_dataset.py`: passed all checks over 42 tables / 17,425 rows.
- Ruff is not installed in the isolated execution environment; lint/format checks are unverified and must run in CI.
- No new database migration was introduced, so PostgreSQL migration execution was not rerun for these pure domain additions.

## 5. Deliberate non-goals / not yet integrated

This iteration is a domain kernel, not a complete Guardian or Commons product feature. It does not yet provide authenticated HTTP routes, document uploads, object storage, database persistence, a Meta model API gateway, OCR, an evidence vault, Guardian case lifecycle, durable GENIEA missions/checkpoints, KRN graph persistence, Commons marketplace APIs, merchant/provider adapters, payment or payout settlement, or MAKOS UI.

Model-extracted values must be supplied by a future adapter with source spans and versioned extraction metadata. Domain review results must be persisted with user ownership and audit in a later vertical integration. External actions remain approval-gated.

## 6. Acceptance for next integration slice

1. Document intake must validate file size, type/signature, owner and retention policy; calculate SHA-256; never execute embedded content.
2. Extraction must return a typed schema with document hash, page/region locator, model identifier, prompt/schema version and confidence for each material field.
3. Deterministic domain review must run after extraction and be able to abstain.
4. Persist the document, evidence references, Guardian case, findings and state transitions in owner-scoped storage with an audit trail.
5. Expose authenticated routes and an observable case timeline in MAKOS.
6. Add a Meta model gateway behind a provider-neutral interface; run a measured extraction task rather than a decorative chat prompt.
7. Run Python 3.12/3.13, SQLite migration lifecycle, PostgreSQL 16 service tests and security/authorization tests in CI.

## 7. Remote status

This iteration is merged remotely in PR #3. The GitHub App installation still appears under `kareem1207`, not the repository owner account `20233-CM-031`; current Iteration 04 branch creation attempts return 403. Do not copy future candidates directly onto `main`.
