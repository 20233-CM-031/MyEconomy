# Iteration 05 — Personal Mode: First Useful Session

**Delivery type:** additive local overlay for `20233-CM-031/MyEconomy`  
**Target baseline:** `60fa93d191fcd6566719db553d4628905a0b64f7`  
**Status in this package:** implemented as an unmerged engineering candidate; user applies and tests it locally.

## Problem

The repository persists owner-scoped financial accounts, transactions and recurring obligations, but the first-user path currently requires a person to assemble API calls and inspect cashflow themselves. The product promise is broader: Personal Mode should produce a useful, private first-session review without depending on bank linking or Commons network scale.

## Delivered slice

1. `GET /api/v1/personal/power-report` reads the authenticated owner's persisted records.
2. The API composes the existing posted-only cashflow service, active account metadata, potential duplicate transaction links and active recurring obligations.
3. Pure domain logic emits prioritized, evidence-indexed findings for missing data, unclassified income, negative net cashflow, essential-cost pressure, potential duplicate transactions and due/overdue obligations.
4. The report is read-only. It marks potential duplicates as review signals, does not assume a refund or saving, does not call external parties, does not require Commons, and always reports `verified_value_created = 0`.
5. `scripts/awnnora_first_user_journey.py` orchestrates local registration/verification/login, idempotent synthetic persona loading through the existing service path, and the Power Report API call.
6. Optional Guardian manual-structured-field demo is opt-in only. It is clearly not OCR and does not send a provider message.
7. A deterministic scenario laboratory adds 46 product-level templates and 1,150 generated runs (25 replicas each by default), plus a scenario catalog, manifest and independent invariant validator.

## Domain invariants

- All records are read under the authenticated owner ID; no household-membership shortcut is introduced.
- Only `POSTED` transactions are included by the existing cashflow service.
- `INCOME`, `EXPENSE` and `REFUND` treatments retain existing semantics. Transfers and ignored entries remain excluded.
- Currency is explicit; supported currency precision is checked using the repository's existing money primitives.
- `essential + discretionary = gross expenses` and `net = income - gross expenses + refunds` must reconcile.
- Potential duplicate references are signals, not confirmed double charges.
- Obligations are schedule records, not payment mandates or confirmation of the provider's amount.
- No external state mutation, payment, claim, benefit award or provider contact occurs.
- Synthetic fixture outcomes never count as VIVC.

## API contract

`GET /api/v1/personal/power-report`

Required query parameters:
- `period_start=YYYY-MM-DD`
- `period_end=YYYY-MM-DD`

Optional parameters:
- `currency=INR` (default)
- `as_of=YYYY-MM-DD` (default: current date in the server local timezone)
- `obligation_horizon_days=30` (1–90)

Requires an authenticated, email-verified account. Response includes aggregate amounts, record counts, findings with source references, report limitations and explicit safety flags.

## Non-goals / not delivered

- Not a full Personal Economic Twin, financial adviser, credit score or guarantee of a complete balance sheet.
- No automated classification of ignored/unclassified credits.
- No model/LLM integration, forecasting, budget planner, eligibility decision, opportunity sourcing or payment action.
- No claim that possible duplicate rows are actual duplicate charges.
- No new account aggregator/bank integration.
- No production hardening of Guardian document uploads; files remain `STORED_UNSCANNED` until a real fail-closed scanner pipeline is delivered.
- Scenario runs are synthetic simulations, not execution traces from live services.

## Acceptance and local verification

Package-level checks actually run before delivery:
- `tests/test_personal_power.py`: 5 tests passed under Python 3.13.
- Python bytecode compilation of the overlay passed.
- Scenario generator: 46 templates × 25 replicas = 1,150 runs.
- Independent scenario validator: passed all generated invariants.

Not verified in this package environment:
- Full repository test suite against the target checkout (the repository itself was not cloned into this container).
- Route integration against a migrated target SQLite/PostgreSQL database.
- Ruff lint/format (Ruff was not installed here).
- Live SMTP, PostgreSQL, bank, partner, Meta model or payment integration.

## Manual integration gate

The additive overlay script inserts one import and one `include_router` call into `src/myeconomy/main.py`. It refuses to overwrite a conflicting path or apply against a different HEAD unless the user explicitly passes `--allow-different-head`. It never commits or pushes.
