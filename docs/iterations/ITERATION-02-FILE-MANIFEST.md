# Iteration 02 File Manifest

This manifest describes the exact changed files relative to merged Iteration 01 on `main` (`e25abcffb345fc0a6315114b04c18e8c57a026e6`). No existing files are deleted.

| Repository path | Change | Responsibility / notable symbols | Verification |
|---|---|---|---|
| `.github/workflows/ci.yml` | Modified | Adds the independent 42-table synthetic corpus validator to both Python-version CI jobs, so schema/export/document integrity is checked on every branch and PR run. | `demo_data/synthetic_v1/validate_dataset.py` CI step. |
| `src/myeconomy/domain/financial.py` | Added | Canonical `ParsedTransaction`, bounded `parse_transaction_csv`, exact minor-unit conversion, header/row validation, transaction fingerprint. | Covered by API/domain import tests and dataset seed smoke. |
| `src/myeconomy/domain/errors.py` | Modified | Adds safe financial data validation and idempotency conflict application errors. | API status/error tests. |
| `src/myeconomy/application/financial.py` | Added | Account ownership, active-account enforcement, atomic import, idempotency, provider-status reconciliation state machine, duplicate policy, persisted cashflow, obligation create/list, batch inspection. | `tests/test_financial_data.py`. |
| `src/myeconomy/infrastructure/models.py` | Modified | Adds `FinancialAccount`, `TransactionImportBatch` (including `updated_count`), `FinancialTransaction`, `RecurringObligation` with owner/account/currency composite constraints. | `Base.metadata.create_all`, Alembic and API tests. |
| `migrations/versions/f2e9c7a4d821_financial_data_plane.py` | Added | Four financial tables, batch insert/update counters, unique indexes, FK scope, CHECK constraints and transaction financial-fact immutability plus monotonic status-transition guards (SQLite/PostgreSQL). | SQLite upgrade/downgrade/re-upgrade and direct trigger test; PostgreSQL offline SQL generated, live CI pending. |
| `src/myeconomy/api/financial_schemas.py` | Added | Strict Pydantic request/response DTOs; import response exposes `updated_count`. | Route tests/OpenAPI app startup. |
| `src/myeconomy/api/financial_routes.py` | Added | Versioned account, import, batch, transaction, cashflow and obligation endpoints; streaming 2 MiB body guard; timestamps normalized to UTC across SQLite/PostgreSQL. | 56-test suite, including live FastAPI TestClient calls. |
| `src/myeconomy/main.py` | Modified | Registers financial router and updates app version/description. | App/API tests. |
| `tests/conftest.py` | Modified | Advances test Alembic marker to `f2e9c7a4d821` and installs SQLite test trigger for transaction immutability/status-transition lifecycle. | All tests. |
| `tests/test_financial_data.py` | Added | Account, import semantics, idempotency, provider-reference conflict, atomic rejection, duplicate heuristic, owner isolation, upload limits, obligations, direct composite FK enforcement, status reconciliation, terminal-state rejection, direct database immutability, conflicting same-file provider states, conservative treatment and currency header guard. | 15 new tests; total suite 56 passed. |
| `scripts/seed_synthetic_customer.py` | Added | Safe local loader for one synthetic persona into an existing verified user; counts actual inserts separately from idempotent replayed rows. | Two-run SQLite integration smoke with stable final row counts. |
| `scripts/verify_postgres_audit.py` | Modified | Extends PostgreSQL migration verification to check allowed provider status progression and reject terminal-state reactivation. | Script compiles; live PostgreSQL 16 execution pending this branch's CI. |
| `README.md` | Modified | Current Iteration 02 scope and API routes. | Manual documentation review. |
| `docs/PROJECT_MEMORY.md` | Modified | Durable implemented status updated through Iteration 02; future features remain clearly marked. | Cross-checked against source. |
| `docs/PROJECT_STATUS.md` | Modified | Live Git state, CI, code state, tests, blockers and next objective reconciled. | GitHub read-only inspection + local tests. |
| `docs/CODEBASE_MAP.md` | Modified | New financial domain/application/API/model/migration/test/seed call paths. | Cross-checked against source files. |
| `docs/FEATURE_CATALOG.md` | Modified | Financial data/import/cashflow/seed status moved to implemented/partial with evidence. | Cross-checked against code/tests. |
| `docs/SYNTHETIC_DEMO_DATASET.md` | Modified | Documents guarded one-person loader, conservative CSV classification and remaining fixture-only features. | Manual review. |
| `docs/DEMO_PLAYBOOK.md` | Modified | Adds a live pending-to-posted reconciliation demonstration and safe unclassified-row behavior. | Matched to API and automated tests. |
| `docs/HACKATHON_SCORECARD.md` | Modified | Updates technical-depth evidence against the judging rubric, with honest current feature boundaries. | Reconciled to implementation. |
| `PUSH_TO_GITHUB.md` | Modified | Current main base, overlay application, validation, commit and PR instructions. | Manual command review; actual remote write remains owner-authenticated. |
| `demo_data/synthetic_v1/README.md` | Modified | Adds reproducible loader instructions and replay semantics. | Manual review. |
| `docs/FINANCIAL_DATA_CONTRACT.md` | Added | Normative monetary, transaction, import, ownership and cashflow rules. | Reconciled with domain/app/tests. |
| `docs/decisions/ADR-0003-financial-data-plane.md` | Added | Records architectural choices and rejected alternatives. | Architecture review. |
| `docs/iterations/ITERATION-02.md` | Added | Scope, acceptance, verification and next iteration. | Reconciled to tests. |
| `docs/iterations/ITERATION-02-FILE-MANIFEST.md` | Added | This file. | File inventory. |
| `demo_data/synthetic_v1/api_scenarios/06_financial_data_import.json` | Added | Honest synthetic account-import walkthrough scenario. | JSON parse validation. |

## Apply and push

Always start from the latest merged `main`, not the old Iteration 01 branch:

```powershell
git clone https://github.com/20233-CM-031/MyEconomy.git
cd MyEconomy
git switch -c iteration/02-financial-data-plane
```

Extract the supplied Iteration 02 overlay ZIP into the repository root, preserving paths and overwriting only the listed files. Then:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "[dev]"
alembic upgrade head
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python demo_data/synthetic_v1/validate_dataset.py
git diff --check
git status --short
```

Review the full diff, then commit and push:

```powershell
git add -A
git commit -m "feat: add owner-scoped financial data plane"
git push -u origin iteration/02-financial-data-plane
```

Open a PR into `main`. Do not force-push. Do not include local `.env`, database files, credentials or user financial data. The current connected GitHub integration returned HTTP 403 when asked to create the branch, so this push must be performed by the owner's authenticated Git client.
