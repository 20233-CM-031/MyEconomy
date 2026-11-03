# Codebase Map — Iteration 00

> Reconciled against the current local tree on 2026-11-03. This document describes the actual files and call paths, not future target modules.

## 1. Runtime call path

```text
HTTP request
  -> FastAPI app (`src/myeconomy/main.py`)
  -> versioned router (`src/myeconomy/api/routes.py`)
  -> Pydantic request validation (`src/myeconomy/api/schemas.py`)
  -> application use case (`src/myeconomy/application/cashflow.py`)
  -> pure domain calculator (`src/myeconomy/domain/cashflow.py`)
  -> exact money helpers (`src/myeconomy/domain/money.py`)
  -> summary mapped into response DTO
  -> HTTP JSON response
```

The current service is stateless. Request data is not persisted. There are no repository/database/provider adapters in the present source tree.

## 2. Root and operational files

| Path | Purpose | Notes |
|---|---|---|
| `README.md` | Project intro, present scope, local run/test instructions | Keep current implementation boundary explicit. |
| `AGENTS.md` | Contributor/AI operating rules | Read first for future changes. |
| `pyproject.toml` | Python packaging, dependencies, test/lint configuration | Python `>=3.12,<3.14`; FastAPI, Uvicorn, Pydantic; dev tools pytest/httpx/ruff. |
| `Makefile` | Short install/test/lint/format/run targets | Convenience only; commands remain reproducible manually. |
| `Dockerfile` | Minimal Python 3.12 container build | Does not include DB or migrations because none exist yet. |
| `.env.example` | Non-secret environment sample | Iteration 00 has no secret-backed integrations. |
| `.gitignore` | Ignores venv, caches, `.env`, sqlite files, OS metadata | Extend when build artifacts are added. |
| `.github/workflows/ci.yml` | GitHub Actions CI on main, iteration branches and PRs | Installs package, runs Ruff and pytest. |

## 3. Python package map

### `src/myeconomy/main.py`

Composition root. `create_app()` creates FastAPI metadata, mounts the API router, and defines:
- `GET /health/live`: process liveness, returns `{"status":"alive"}`.
- `GET /health/ready`: currently static readiness, returns `{"status":"ready"}` because there are no external dependencies yet.

`app = create_app()` exports the ASGI application used by Uvicorn and tests. When a database/queue is added, readiness must perform bounded dependency checks; liveness should remain a process-health signal.

### `src/myeconomy/api/routes.py`

HTTP adapter. Creates router with prefix `/api/v1` and exposes:
- `POST /cashflow/analyze` with `CashflowAnalysisRequest` and `CashflowAnalysisResponse`.

It maps validated Pydantic entry DTOs into domain `CashflowEntry` values, calls `run_cashflow_analysis`, and maps the returned immutable summary into response DTOs. Keep route code thin; no financial formulas or persistence logic should be added here.

### `src/myeconomy/api/schemas.py`

Boundary validation and transport contracts:
- `CashflowEntryInput`: date, positive Decimal amount, category, essential flag; rejects unknown fields and trims category whitespace.
- `CashflowAnalysisRequest`: 3-letter currency code, inclusive period, income/expense arrays capped at 5,000 each; rejects unknown fields, reversed periods, entries outside the period, unsupported currencies and amounts with excess currency precision.
- `CategoryTotalResponse` and `CashflowAnalysisResponse`: response representation.

`calculation_note` explicitly says net cashflow is based only on submitted entries and is not a verified bank balance or complete savings measure. Currency validation delegates to `domain.money.currency_exponent`. `quantize_amount` is also used at the request boundary to reject precision loss.

### `src/myeconomy/application/cashflow.py`

Application use case. `run_cashflow_analysis(...)` currently delegates to the pure domain `analyze_cashflow`. This layer is intentionally thin now; future orchestration belongs here (authorization, repositories, unit-of-work, domain services), while invariants remain in domain types/functions.

### `src/myeconomy/domain/money.py`

Exact monetary primitives:
- `CURRENCY_EXPONENTS`: curated registry for AED, AUD, BHD, CAD, CHF, EUR, GBP, INR, JPY, KWD, OMR, QAR, SAR, SGD and USD.
- `MoneyInputError`: controlled invalid-money exception.
- `currency_exponent(currency)`: normalizes code to uppercase and rejects unsupported codes.
- `quantize_amount(amount, currency)`: finite positive amount validation, currency minor-unit normalization with `Decimal`/`ROUND_HALF_UP`, and rejection if normalization would change the input.
- `quantize_total(amount, currency)`: rounds calculated totals to currency precision.

This is not a complete live ISO-4217 registry. Check an authoritative current source before adding currencies. Never use float for monetary arithmetic. FX conversion is not implemented.

### `src/myeconomy/domain/cashflow.py`

Pure calculation core:
- `CashflowEntry`: immutable input record (`occurred_on`, `amount`, `category`, `essential`).
- `CategoryTotal`: category and aggregate amount.
- `CashflowSummary`: immutable output values.
- `_validate_entries(...)`: enforces inclusive period boundaries, currency precision, positive finite money and nonblank normalized categories.
- `analyze_cashflow(...)`: validates dates and entries; computes income, expenses, essential/discretionary expense totals, net cashflow, category totals and sorted categories.

Category ordering is descending total; ties use case-insensitive category ordering. The `savings_rate_percent` field currently computes `net_cashflow / income_total * 100`, quantized to two decimal places; it can be negative and is `None` when income is zero. This is a **net-cashflow-to-income ratio**, not a verified household savings rate. Future API/domain cleanup should consider renaming it to avoid implying actual savings; do so through an explicit compatibility/versioning decision.

### Package initializers

`src/myeconomy/__init__.py`, `api/__init__.py`, `application/__init__.py`, `domain/__init__.py` contain package docstrings only. The domain initializer states the desired dependency rule: no FastAPI or infrastructure dependency.

## 4. Test map

| Path | Coverage |
|---|---|
| `tests/test_cashflow_domain.py` | Totals/category order, zero-income/deficit, out-of-period rejection, JPY zero-decimal precision, INR excess-precision rejection, KWD three-decimal precision. |
| `tests/test_api.py` | Health endpoints, successful analysis endpoint, period validation response, unknown-field rejection, category whitespace normalization. |

Recorded baseline: `PYTHONPATH=src pytest -q` -> 11 passed. Re-run tests in the current environment before relying on that historical result.

## 5. Documentation map

| Path | Responsibility |
|---|---|
| `docs/PROJECT_MEMORY.md` | Durable product vision, complete feature context, architecture intent, trust boundaries, demo and source-of-truth rules. |
| `docs/CODEBASE_MAP.md` | This file: actual code responsibilities and runtime path. |
| `docs/FEATURE_CATALOG.md` | Per-feature status ledger (implemented/planned/not started). |
| `docs/PROJECT_STATUS.md` | Dated factual status and next engineering slice. |
| `docs/AI_COLLABORATION_PROTOCOL.md` | How future AI sessions inspect, change and document the repo. |
| `docs/PRODUCT_VISION.md` | Product-facing mission, features, Commons, value model and demo framing. |
| `docs/ARCHITECTURE.md` | Logical module boundaries, request flow, persistence/AI/security target patterns and implementation limit. |
| `docs/ENGINEERING_STANDARDS.md` | Non-negotiable coding, money, AI, failure and Git rules. |
| `docs/ITERATION_PLAN.md` | Iteration sequence and acceptance approach. |
| `docs/VERIFICATION.md` | Previously recorded commands, tests, smoke test and environment limitations. |
| `docs/decisions/ADR-0001-modular-monolith.md` | Decision record for starting with a modular monolith. |

## 6. Current dependency direction

`api -> application -> domain`.

`domain` must not import `api`, FastAPI, Pydantic, database clients, queues, LLM SDKs or external provider SDKs. Future infrastructure adapters implement application-defined ports and are wired at the composition root. Do not allow one domain module to reach directly into another module's persistence implementation.

## 7. Gaps / next refactor candidates

1. The current currency registry is curated and static; make its supported scope/version explicit and add authoritative update tests before expanding it.
2. `savings_rate_percent` naming can mislead; consider a versioned rename to `net_cashflow_rate_percent`.
3. `GET /health/ready` is static; add bounded dependency probes when external dependencies exist.
4. Error response structure is currently FastAPI/Pydantic default; define stable public error codes before clients depend on it.
5. There is no database, authentication, tenancy, consent, audit log, rate limit, idempotency, pagination or import provenance yet.
6. Expand tests for malformed numeric input, extremely large totals, duplicate entries, category normalization edge cases, date boundaries and response schema stability.

## 8. How to inspect this code in a new session

Run `find src tests -type f -maxdepth 5 -print`, read all current source and tests, then run `pytest`, `ruff check src tests` and `ruff format --check src tests`. Update this map whenever a module, public route, domain invariant or test responsibility changes.
