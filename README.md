# MyEconomy — Personal Economic Agency Platform

**Working product category:** Personal Economic Agency & Collective Opportunity Intelligence
**Product brand:** Not selected. `MyEconomy` is the repository and working project name.

> Intelligence for the individual. Power for everyone.

The final customer-facing name will be selected later. Previous naming suggestions have not been approved; see `docs/PROJECT_MEMORY.md` for the naming constraints.

This repository is the engineering foundation for a system that helps people protect their interests, recover value, discover opportunities, access resources, build income and enterprises, and—only with explicit consent—coordinate collective demand and resources.

The system is being developed through small, verifiable iterations. No feature is considered complete because a screen exists or an AI model returns plausible prose. It is complete only when its domain logic, API behavior, failure handling, security boundaries, tests and runtime behavior meet documented acceptance criteria.

## Iteration 00 — Engineering Foundation + Cashflow Analysis Slice

This initial slice provides:

- A framework-independent deterministic cashflow calculation core.
- A typed HTTP API with strict request validation.
- Currency-specific minor-unit precision for supported currencies.
- Period-bound validation to prevent accidentally including out-of-period entries.
- Health and readiness endpoints.
- Unit and API tests for normal, boundary and invalid-input cases.

**Important scope boundary:** This iteration does not connect to banks, store personal financial records, make payments, confirm government-benefit eligibility, or claim verified savings. It calculates only from the data explicitly supplied in a request. Those capabilities require their own integrations, consent flows and acceptance tests.

## Run locally

Python 3.12 or 3.13 is supported.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn myeconomy.main:app --reload
```

API documentation: `http://127.0.0.1:8000/docs`

Health: `GET http://127.0.0.1:8000/health/live`
Readiness: `GET http://127.0.0.1:8000/health/ready`
Cashflow analysis: `POST http://127.0.0.1:8000/api/v1/cashflow/analyze`

Example request:

```json
{
  "currency": "INR",
  "period_start": "2026-11-01",
  "period_end": "2026-11-30",
  "incomes": [
    {"occurred_on": "2026-11-01", "amount": "50000.00", "category": "salary"}
  ],
  "expenses": [
    {"occurred_on": "2026-11-03", "amount": "18000.00", "category": "rent", "essential": true},
    {"occurred_on": "2026-11-04", "amount": "6000.00", "category": "groceries", "essential": true},
    {"occurred_on": "2026-11-05", "amount": "4000.00", "category": "transport", "essential": false}
  ]
}
```

## Test

```bash
pytest
```

## Engineering approach

Start with `AGENTS.md`, then read `docs/PROJECT_MEMORY.md`, `docs/PROJECT_STATUS.md`, `docs/FEATURE_CATALOG.md` and `docs/CODEBASE_MAP.md`. Additional design and implementation guidance is in `docs/ARCHITECTURE.md`, `docs/PRODUCT_VISION.md`, `docs/ITERATION_PLAN.md`, `docs/ENGINEERING_STANDARDS.md` and `docs/decisions/ADR-0001-modular-monolith.md`.
