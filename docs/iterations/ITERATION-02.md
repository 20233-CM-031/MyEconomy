# Iteration 02 — Financial Data Plane v1

**Date:** 2026-11-04
**Status:** Implemented locally; 56 tests pass; remote push pending owner Git client because connector branch creation returned 403.
**Base:** Current `main` at `e25abcffb345fc0a6315114b04c18e8c57a026e6` (merged Iteration 01 PR #1).
**Intended branch:** `iteration/02-financial-data-plane`.

## 1. Problem

Iteration 00 calculated cashflow only from caller-provided request data. Iteration 01 established verified accounts, ownership, household boundaries, consent and audit. The system cannot yet ingest, persist or query a person's own financial activity. This prevents us from building meaningful Day-One Personal Power and Guardian workflows.

## 2. Goal

Build a reliable first financial data plane that:

- persists the authenticated person's own financial accounts, transactions and recurring obligations;
- imports a realistic CSV statement safely and deterministically;
- prevents cross-owner/account/currency mixing at both application and database layers;
- makes retries safe and source provenance auditable;
- produces a truthful posted-only single-currency cashflow read model;
- runs against the existing synthetic dataset without creating fake login accounts.

## 3. In scope

- Four relational tables and one Alembic migration.
- Integer minor-unit amount storage and currency code.
- Strict pure CSV parser and transaction normalization.
- Owner-scoped account, import, transaction, cashflow and obligation APIs.
- Import byte hash, idempotency, provider reference constraints and advisory duplicate links.
- Atomic whole-batch rejection and append-only audit metadata.
- Local-only one-person synthetic data seeder.
- Tests, domain contract, architecture decision, CI synthetic-corpus validation, project memory and codebase map updates.

## 4. Non-goals

- Open banking / RBI Account Aggregator integration or bank credential collection.
- Payments, UPI initiation, automatic debits or live provider calls.
- Budget engine, allocation forecasts, goals, net-worth or balance reconciliation.
- Bill document storage/OCR, Guardian claims, benefits, employment/skills marketplace or Commons matching.
- RAG, graph database, Meta model gateway, agent mission/checkpoint service or multimodal model execution.
- Production security certification, field-level encryption/KMS or retention/export/erasure automation.

## 5. Domain invariants

1. Every financial record is owned by one user. Membership in a household does not change ownership.
2. Account, transaction and linked obligation currency must match exactly.
3. Money is never binary float. Persist positive integer minor units + currency; direction holds sign semantics.
4. `INCOME` requires CREDIT; `EXPENSE` requires DEBIT; `REFUND` requires CREDIT.
5. Only POSTED records affect the cashflow period. REFUND offsets expense, not income; TRANSFER/IGNORE are excluded.
6. CSV upload maximum is 2 MiB, 10,000 data rows and 32 columns.
7. Same user/idempotency key/content replays the previous batch. Same key/different content or account conflicts.
8. A repeated provider external reference with the same normalized fingerprint is skipped; a different payload rejects the batch.
9. Fingerprint similarity is not proof: preserve candidate row and link it for review.
10. Any invalid row/conflicting external reference rejects the whole batch, inserting zero transactions.
11. Uploaded CSV bytes are not retained.
12. A recurring obligation is an expected schedule, not a posted payment, mandate or proof of payment.
13. The synthetic loader runs only in development/test/demo, checks `SYNTHETIC_FIXTURE`, requires an existing verified user and never creates fake login identities.

## 6. Data model

- `FinancialAccount`: owner, account type, currency, masked reference, opening balance in minor units, source identity.
- `TransactionImportBatch`: owner, account, idempotency key, source SHA-256, safe filename, counts, status and validation errors.
- `FinancialTransaction`: owner/account/batch, date/time, integer amount, currency, direction, cashflow treatment, category, description, counterparty, provider reference, status, essential flag, fingerprint and possible duplicate link.
- `RecurringObligation`: owner, optional linked account, payee/category, integer amount/currency, frequency, due-day hint, first/next due dates, autopay label and source identity.

Composite foreign keys bind transaction/import/obligation rows to the same account owner and currency. The possible-duplicate link is also constrained to the same owner/account/currency.

## 7. API

- `POST /api/v1/financial/accounts`
- `GET /api/v1/financial/accounts`
- `POST /api/v1/financial/accounts/{account_id}/imports/csv`
- `GET /api/v1/financial/imports/{batch_id}`
- `GET /api/v1/financial/accounts/{account_id}/transactions`
- `GET /api/v1/financial/cashflow`
- `POST /api/v1/financial/obligations`
- `GET /api/v1/financial/obligations`

All require verified auth. CSV requires `Idempotency-Key`. The body is streamed with a request-size guard.

## 8. Synthetic data integration

`scripts/seed_synthetic_customer.py --user-email <verified-local-user> --customer-id CUS00001` maps selected fixture accounts to `FinancialAccount.source_external_id`, imports transactions through the same application function, and creates recurring obligations with stable source IDs. It does not create the synthetic customer as an application login.

Local SQLite smoke evidence: first seed created 2 accounts, inserted 91 transactions and created 5 recurring obligations. Re-run reused 2 accounts, replayed both import batches and reused all 5 obligations; row counts did not increase.

## 9. Verification

- `PYTHONPATH=src pytest -q`: **56 passed** (including provider `PENDING -> POSTED`, prohibited reactivation after reversal, conflicting same-file provider states, safe unclassified-default behavior, INR header/account currency enforcement, timezone normalization and financial-fact immutability).
- `python -m compileall -q src tests migrations scripts`: passed.
- SQLite migration: upgrade to head, downgrade to base, upgrade to head: passed, including transaction immutability/status-transition guard lifecycle up/down.
- PostgreSQL offline migration SQL generation passed and emitted the transaction immutability/status guard function/trigger; live PostgreSQL 16 execution is pending this branch's CI.
- Dataset independent validator: passed locally and added as a required step to both Python-version CI jobs.
- Synthetic seed: first run created 2 accounts, 91 transactions and 5 obligations; replay run created 0 new rows, reported 2 idempotent import-batch replays / 91 historical rows and reused 5 obligations. Final counts remained 2 accounts, 91 transactions, 5 obligations and 2 batches.
- Ruff: unavailable in the isolated local runtime; result is unverified. Must be run in GitHub Actions after push.
- PostgreSQL: the merged Iteration 01 main CI proves its own migrations/audit triggers on PostgreSQL 16, but this new migration still needs its own PostgreSQL CI execution.

## 10. Acceptance status

- [x] Owner-scoped accounts and transaction records.
- [x] Database composite keys for owner/account/currency boundaries.
- [x] Exact monetary minor-unit storage and currency validation.
- [x] Strict bounded CSV parser and atomic validation failure.
- [x] Batch and provider-reference idempotency.
- [x] Monotonic provider lifecycle reconciliation with separate update count, audit trail and SQLite/PostgreSQL triggers.
- [x] Conservative unclassified default (`IGNORE`) and currency-specific `amount_inr` guard.
- [x] Possible duplicate review signal without silent deletion.
- [x] Posted/refund/transfer/pending cashflow treatment.
- [x] Recurring obligations distinct from posted transactions.
- [x] Synthetic seeder is guarded and idempotent for one verified user.
- [x] Tests and memory map updated.
- [ ] Ruff check/format on this new branch.
- [ ] PostgreSQL 16 CI for this new migration and transition trigger.
- [ ] Concurrency/race tests for simultaneous import retries/provider references.

## 11. Next iteration

Iteration 03 should turn the durable personal financial substrate into a user-visible Day-One Personal Power / Guardian workflow. Start with a synthetic invoice or bill upload, extract source-grounded facts with a suitable Meta model, validate arithmetic and compare prior records deterministically, show evidence/uncertainty, and produce a draft action requiring approval. Do not claim a real bill correction, refund or customer outcome.


## 12. Final local verification (2026-11-04)

- Re-ran `PYTHONPATH=src pytest -q`: **56 passed**.
- Re-ran `PYTHONPATH=src python -m compileall -q src tests migrations scripts`: passed.
- Re-ran SQLite Alembic `upgrade head -> downgrade base -> upgrade head` against a fresh temporary database: passed, including guard creation/removal/recreation.
- Re-generated PostgreSQL offline migration SQL and confirmed the financial transaction immutability/status guard function and trigger are present. This is SQL-generation evidence only; live PostgreSQL 16 execution of the Iteration 02 migration remains pending its GitHub Actions branch run.
- Re-ran the synthetic dataset independent validator: all checks passed across 42 entity tables / 17,425 rows / 12 multimodal documents.
- Re-ran the one-person synthetic seed against a fresh temporary SQLite database: first run created 2 accounts, inserted 91 transactions and created 5 obligations; second run inserted 0 and updated 0 transactions, replayed 2 batches / 91 historical rows and reused 5 obligations. Final counts remained 2 accounts, 91 transactions, 5 obligations and 2 import batches.
- Ruff was not available in this isolated runtime; rely on local Ruff and the new branch CI before merge.
