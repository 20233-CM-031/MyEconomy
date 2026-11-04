# Financial Data Contract — Iteration 02

**Status:** Implemented v1 CSV/manual persistence slice. Bank connectivity, payment rails and shared/Commons access are not implemented.

This document defines the canonical semantics of the first persisted financial data plane. API, importer, tests and future agent tools must obey these rules. When the contract changes, update this document, the domain module, migration, tests and `docs/CODEBASE_MAP.md` together.

## 1. Ownership and trust boundary

- Every financial account, transaction, import batch and recurring obligation has one `owner_user_id`.
- API access requires an active authenticated session and verified email.
- Reads and writes filter by the exact authenticated owner. Non-owner resource lookups return 404 to avoid disclosing another user's resource existence.
- A household membership does not grant access to account or transaction records.
- A user's own records do not require household consent. Any future cross-person/household/partner/Commons read or export must call the exact `require_active_consent` check in the same database transaction as the protected access, with a purpose, category, recipient and expiry. This future sharing path does not exist in Iteration 02.
- Audit records contain action, resource and hash/count metadata; never raw uploaded statement bytes, passwords, session tokens or raw personal financial history.

## 2. Monetary representation

- Persisted amount: positive integer `amount_minor` (BIGINT) plus ISO-like 3-letter `currency` code.
- Sign is represented by `direction`, not by a negative transaction amount.
- Currency minor-unit exponent is sourced from the current curated registry in `domain/money.py`; this is not yet a live/full ISO 4217 data service.
- Decimal input is converted without precision loss. No float is used for money. Values above the conservative signed-BIGINT minor-unit ceiling are rejected.
- Each transaction and each account-linked obligation must match the currency of the linked account through composite foreign keys.
- The cashflow API requires exactly one currency. It never adds INR to USD or performs implicit FX. A future FX feature must store rate, source, timestamp, method, base/quote currencies and rounding policy as a separate auditable conversion record.

## 3. Transaction vocabulary and truth table

`direction`: `CREDIT` or `DEBIT`.

`cashflow_treatment`: `INCOME`, `EXPENSE`, `REFUND`, `TRANSFER`, `IGNORE`.

`status`: `POSTED`, `PENDING`, `REVERSED`, `VOID`.

| Treatment | Required direction | Persisted cashflow effect when status is POSTED |
|---|---|---|
| INCOME | CREDIT | Adds to income |
| EXPENSE | DEBIT | Adds to gross expenses |
| REFUND | CREDIT | Reduces expenses; never adds to income |
| TRANSFER | CREDIT or DEBIT | No income/expense effect |
| IGNORE | CREDIT or DEBIT | No income/expense effect |

Only POSTED rows are included. Pending, reversed and void rows remain visible in the ledger but are excluded from period cashflow. Database checks enforce direction/treatment invariants for income, expenses and refunds; parser and application logic enforce the same policy before persistence.

The transaction amount is always positive. The importer must not infer a negative value from a debit string; the provider's debit/credit field is authoritative. A statement that reports only signed amounts needs a separate, explicit adapter with a tested sign convention.

## 4. Import request contract

`POST /api/v1/financial/accounts/{account_id}/imports/csv`

Required:
- Verified bearer session.
- `Content-Type`: `text/csv`, `application/csv`, `application/octet-stream` or `text/plain`.
- `Idempotency-Key`: 1–128 printable characters.
- Raw CSV bytes in request body; maximum 2 MiB.

Optional:
- `X-Filename`, sanitized to a safe basename and 160 characters.

Parser limits:
- UTF-8, optional BOM.
- At most 32 columns and 10,000 nonblank data rows.
- Duplicate normalized headers are rejected.
- Required canonical fields: date, amount and direction. `cashflow_treatment` is optional, but if omitted the row is stored as `IGNORE` and excluded from cashflow until explicitly classified.
- The specific `amount_inr` header is accepted only for INR accounts; a generic `amount` header is required for other currencies unless an adapter supplies a currency-specific contract.
- Date is ISO-8601 calendar date. `posted_at`, when present, must contain timezone offset and is normalized to UTC.
- Amount uses a decimal point, must be finite/positive, must have no more precision than the account currency, and must fit the integer-minor-unit storage bound.
- A provided row currency must match the account currency. No FX conversion occurs.
- Any invalid row rejects the entire batch. Valid rows from the same file are not partially inserted.

Supported header aliases are in `domain/financial.py`. The current synthetic dataset's `transaction_date`, `amount_inr`, `currency`, `direction`, `cashflow_treatment`, `category`, `counterparty_label`, `reference`, `status` fields are accepted as-is.

## 5. Atomicity, idempotency and duplicate policy

- The importer hashes original request bytes with SHA-256. It stores the hash, sanitized filename, row counts, import state and validation errors; it does not store the uploaded file contents.
- `(owner_user_id, idempotency_key)` is unique. Same owner/key + same account + same content hash returns the original batch (`replayed=true`) and creates no new rows. Same key with different account or content returns 409.
- `external_reference` is unique per owner/account when present. Same reference + same financial fingerprint + same lifecycle state is skipped as a duplicate. Same reference + changed financial content rejects the whole new batch.
- Provider lifecycle updates for the same financial fingerprint are reconciled monotonically: `PENDING -> POSTED|REVERSED|VOID` and `POSTED -> REVERSED|VOID`. `REVERSED` and `VOID` are terminal. Such changes increment `updated_count`, update only lifecycle metadata, and append an audit event. Both the application state machine and SQLite/PostgreSQL database trigger enforce these transitions. A changed amount/date/direction/treatment/category/description/counterparty behind the same reference is rejected.
- Rows without external reference are not silently discarded. A normalized fingerprint can set `potential_duplicate_of_id` and increase the possible-duplicate count; both rows remain persisted for user review.
- The fingerprint is a heuristic, not proof that two purchases are the same. It includes date, integer minor amount, currency, direction, treatment, category, description and counterparty. Financial fact fields are immutable after insertion: amount, date, currency, direction, treatment, category, description, counterparty, provider reference and source identity cannot be edited in place. Only a previously missing `posted_at` may be enriched and the lifecycle status may follow the allowed state graph. Corrections require a separately modelled reversal/compensating entry, not mutation of the imported economic facts.
- Batch outcome, transaction inserts and append-only audit event are committed in one database transaction. If DB constraints fail, the transaction rolls back; retry the same key to reconcile state.

## 6. Import batch states

- `COMPLETED`: all rows processed; may include inserts, lifecycle updates, or duplicate-only input.
- `PARTIAL`: one or more rows inserted and one or more exact provider duplicates were skipped.
- `REJECTED`: malformed CSV, invalid row, forbidden lifecycle transition or conflicting external reference; zero transaction rows inserted or updated from that batch.

Batch counters distinguish `inserted_count`, `updated_count`, `duplicate_count` and `potential_duplicate_count`. A replay of the same idempotency key returns the original counters with `replayed=true`; it does not count those rows as newly inserted by the replay.

Possible-duplicate warnings do not reject the batch; they are persisted as transaction links and counted separately.

## 7. Cashflow read model

`GET /api/v1/financial/cashflow?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&currency=INR`

- owner = authenticated user;
- transaction status = POSTED;
- inclusive date range;
- exact currency filter;
- `income_total = sum(INCOME CREDIT)`;
- `gross_expenses = sum(EXPENSE DEBIT)`;
- `refunds = sum(REFUND CREDIT)`;
- `net_expenses_after_refunds = gross_expenses - refunds` (may be negative if the period contains refunds of earlier-period spending);
- `net_cashflow = income_total - gross_expenses + refunds`;
- essential/discretionary expense components are currently reported before refund allocation; a future category-aware refund allocator must be explicit;
- `net_cashflow_to_income_percent = net_cashflow / income_total * 100`, if income exists.

This is not verified income, bank balance, net worth, available balance or complete savings. Opening balances, unsettled items, omitted accounts, transfers and external statement coverage may materially change a person's true financial position. The UI must show source coverage and date range before presenting an interpretation.

## 8. Recurring obligations

A `RecurringObligation` is an expected future commitment (rent, tuition, insurance, subscription, EMI, etc.). It is not a posted transaction, bank mandate, authorization to debit, or proof a bill was paid. It stores expected amount/currency, frequency, due-day hint, first/next due dates, essential flag, optional linked same-owner/same-currency account, and a source marker. `autopay_enabled` is descriptive input only; no payment initiation or scheduler exists.

## 9. Synthetic fixture loading

`scripts/seed_synthetic_customer.py` loads one selected fixture person into an existing verified local application user, only for `APP_ENV=development|test|demo`. It never creates a fictitious login/user. It checks `SYNTHETIC_FIXTURE`, uses stable fixture IDs/idempotency keys, and can be rerun safely. It currently loads account metadata, transactions and recurring obligations only; other dataset entities await their runtime services.

Never use these fixtures against real bank/provider/payment APIs, production tenants, or as actual user-outcome evidence.

## 10. Known limitations before real-time production

- No live bank connection or Account Aggregator integration; no credentials are collected.
- No opening-balance reconciliation or balance endpoint.
- No transaction correction/delete API; use future reversal/compensating-event semantics.
- No user export/erasure or retention automation yet.
- No field encryption/KMS, production security review or penetration test.
- New Iteration 02 migration still needs PostgreSQL 16 CI service verification on its own branch.
- No FX, category learning, budget allocations or forecast in this slice.
