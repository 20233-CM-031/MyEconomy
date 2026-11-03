# Project Status

**Last reconciled:** 2026-11-03
**Repository:** `20233-CM-031/MyEconomy`
**Remote default branch observed:** `main`
**Local work branch:** `iteration/00-engineering-foundation`
**Product brand:** Not selected (`MyEconomy` remains repository/internal name).

## 1. Verified repository baseline

The GitHub repository was inspected through the connected GitHub integration. At inspection, it had one branch (`main`) and one initial commit (`a3b4eb99de1d3d737ab8126ca6d61cf230f9bb0e`) containing a two-line README (`# MyEconomy` and `meta AI hakathon`). Repository metadata reported public visibility and default branch `main`.

A local project copy was created from that baseline. Local commit history:

```text
e5a4790 feat: establish engineering foundation and deterministic cashflow API
6feb028 chore: mirror remote repository baseline
```

Current local branch: `iteration/00-engineering-foundation`. Local remote `origin` points to `https://github.com/20233-CM-031/MyEconomy.git`.

**Remote write state:** the GitHub connector returned HTTP 403 when attempting to create a remote branch and when attempting repository file writes. Do not describe these local commits as pushed. The user may push from their own authenticated Git client.

## 2. Current implementation

Iteration 00 includes:
- Python package targeting Python 3.12 and 3.13.
- FastAPI application composition root and API router.
- Pydantic v2 request/response schemas with unknown-field rejection.
- Pure domain `Money` and `Cashflow` logic using `Decimal`.
- A curated static 15-currency minor-unit exponent registry.
- Inclusive date-period validation, essential/discretionary expense calculation, category totals and net-cashflow-to-income percentage.
- `/health/live`, `/health/ready` and `POST /api/v1/cashflow/analyze`.
- pytest tests, Ruff config, GitHub Actions CI, Dockerfile, Makefile and engineering docs.

The API accepts caller-provided JSON for a calculation. Nothing is persisted and the endpoint does not read bank data.

## 3. Verification record

The previous local run recorded:
- `PYTHONPATH=src pytest -q`: 11 passed.
- Local Uvicorn HTTP smoke test on `127.0.0.1:8765`:
  - `GET /health/live` -> `{"status":"alive"}`.
  - `GET /health/ready` -> `{"status":"ready"}`.
  - `POST /api/v1/cashflow/analyze` returned expected result for the test request.

The previous environment had no outbound DNS/network access. An isolated editable install could not download build requirements; installation with `--no-build-isolation` against installed build tooling worked. Re-run tests and lint in the next environment; do not rely only on historical verification.

## 4. Explicitly not implemented

No database, migrations, authentication, tenancy, authorization, consent ledger, encryption/key management, bank integration, CSV importer, transaction persistence, budget engine, benefits catalogue/API, complaint submission, provider/merchant integration, payment/payout, sponsorship, agent/LLM runtime, RAG, graph database, Commons network or production deployment exists in Iteration 00.

All such capabilities are design/roadmap items and must not be represented as live in UI or demo.

## 5. Important code-quality notes for next iteration

- Current currency registry is limited and static; verify ISO 4217 source before expanding.
- `savings_rate_percent` currently means `net_cashflow / income * 100`, not verified savings; consider a clearly named ratio in a versioned contract.
- Readiness endpoint is static because there are no dependencies.
- Public error codes and a stable error envelope are not yet defined.
- Add tests for unusually large cumulative totals, malformed numeric strings, duplicates, more boundary dates and schema compatibility.
- No authorization/concurrency tests are relevant yet because persistence and identity are absent; they become mandatory once those exist.

## 6. Next recommended iteration

**Iteration 01 — Identity, Authorization, Consent and Personal Data Ownership.** Before importing financial records or integrating agents, define threat model and ownership boundaries, authenticate users, enforce resource-level authorization, and build auditable purpose-specific consent with revocation. Add PostgreSQL and migrations in the same carefully scoped iteration only after the schema and lifecycle are reviewed.

Acceptance should include cross-user and cross-household access-denial tests, expired/revoked consent tests, audit checks, secure secret handling, migration up/down checks, session lifecycle tests and a reproducible runtime environment.

## 7. Status update rule

Update this file whenever branch, commit, implementation, test status, blockers or next iteration changes. Date every status change. Verify against the live repository and current source tree first.

## 8. Memory-map update verification (2026-11-03)

- Re-read the live remote `README.md`; it still contains only the original two-line project placeholder, so the Iteration 00 implementation and memory docs are not yet on GitHub `main`.
- Re-ran `PYTHONPATH=src pytest -q`: **11 passed**.
- Ruff is configured in `pyproject.toml` and CI but the current execution container does not have the `ruff` executable installed; lint/format checks are therefore **not verified in this run**.
- Python compilation and patch integrity are being checked separately for this memory-map delivery.
- Python bytecode compilation (`python -m compileall -q src tests`) succeeded.
- `git diff --check` succeeded.
- The complete delivery patch was applied to a clean worktree based on the mirrored original README baseline; all 11 tests passed there as well.
- Ruff remains unverified in this runtime because the executable is absent; CI is configured to run it after the branch is pushed.
