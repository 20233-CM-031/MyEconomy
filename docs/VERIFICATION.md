# Iteration 00 Verification Record

Date: 2026-11-03

## Automated tests

Command: `PYTHONPATH=src pytest -q`

Result: **11 passed**.

Coverage includes:
- Income, expense, net cashflow, essential/discretionary split and savings-rate calculation.
- Expense category aggregation and deterministic sort order.
- No-income / deficit behavior.
- Period-bound validation.
- Currency minor-unit precision for zero-, two- and three-decimal currencies.
- Liveness and readiness endpoints.
- HTTP cashflow calculation and invalid request rejection.
- Unknown-field rejection and category normalization.

## Local runtime smoke test

Started Uvicorn on `127.0.0.1:8765`.

- `GET /health/live` returned `{"status":"alive"}`.
- `GET /health/ready` returned `{"status":"ready"}`.
- `POST /api/v1/cashflow/analyze` with INR 50,000 income, INR 18,000 essential expense and INR 4,000 discretionary expense returned INR 22,000 expense, INR 28,000 net cashflow and 56.00% net-cashflow-to-income ratio.

## Environment limitation

The container has no outbound DNS/network access. A standard isolated editable-install attempt could not download build requirements. The project was then installed with `--no-build-isolation` against the already-installed build tooling, imported successfully, and its tests were run. The GitHub connector also rejected branch/file writes with HTTP 403. Therefore the implementation is verified locally but has **not** been pushed to the remote repository.
