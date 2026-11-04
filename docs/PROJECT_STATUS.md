# Project Status

**Last reconciled:** 2026-11-04
**Repository:** `20233-CM-031/MyEconomy`
**Remote default branch:** `main`
**Remote `main` HEAD:** `e25abcffb345fc0a6315114b04c18e8c57a026e6` — merge of PR #1, `iteration/01-trust-and-synthetic-demo-data`
**Iteration 01 branch HEAD:** `baade0b3c920ad325d011de2e41eefb81d8dda57` (now one commit behind `main` because PR #1 was merged)
**Current delivery:** Iteration 02 — Financial Data Plane v1 (prepared locally; not yet pushed)
**Intended next branch:** `iteration/02-financial-data-plane`
**Product brand:** Not selected. `MyEconomy` remains repository/internal project name.

## 1. Live GitHub state (verified 2026-11-04)

The repository was re-read after the owner updated GitHub. PR #1 merged successfully into `main` at `e25abcffb345fc0a6315114b04c18e8c57a026e6`. `main` is one commit ahead of the old Iteration 01 feature branch, with no code divergence indicated by the merge comparison. The merged main CI run `41701730347` completed successfully:

- `tests (3.12)`: Ruff lint, Ruff format, pytest and SQLite migration upgrade/downgrade all passed.
- `tests (3.13)`: Ruff lint, Ruff format, pytest and SQLite migration upgrade/downgrade all passed.
- `postgres-migrations`: PostgreSQL 16 service-backed Alembic upgrade, audit-trigger verification, downgrade and re-upgrade passed.

The Iteration 02 working copy was reconciled against the merged Iteration 01 tree. Do not use the old feature branch as the new base; create the next branch from current `main`.

The connected GitHub integration can read this repository, but its branch-creation request returned HTTP 403 (`Resource not accessible by integration`). Therefore Iteration 02 is not pushed, no remote branch is claimed, and no remote commit exists for this delivery. The archive/overlay and exact Git commands are provided for the owner's authenticated Git client.

## 2. Implemented capabilities

### Iteration 00 — deterministic cashflow foundation

- Python 3.12/3.13 FastAPI application with Pydantic contracts, health and readiness.
- Framework-independent `Decimal` money/cashflow calculation over caller-supplied request entries.
- Curated currency precision registry; no FX conversion.

### Iteration 01 — identity, household trust and consent

- SQLAlchemy/Alembic persistence for users, verification challenges, opaque sessions, households, invitations, consent grants and audit events.
- Argon2id password hashing, digest-only bearer and email-verification tokens, verified-email gates, invitation expiry/revocation and consent lifecycle.
- Append-only audit events protected at ORM and database-trigger layers.
- Merged into `main` through PR #1. The merged GitHub Actions run passed Python 3.12/3.13 and PostgreSQL 16 migration/audit verification.

### Iteration 02 — financial data plane v1 (local implementation, 2026-11-04)

- Owner-scoped financial account metadata, transaction import batches, persisted transaction ledger and recurring obligations.
- Money stored as integer minor units (`BIGINT`) with currency code. Transaction and obligation currencies are constrained to their linked account by composite foreign keys; no implicit FX.
- CSV upload is streamed with a 2 MiB bound; the domain parser caps 10,000 data rows and 32 columns, requires UTF-8, rejects duplicate normalized headers and validates dates, currency, Decimal precision, direction, treatment, status, essential flag and lengths.
- Import batches store SHA-256, sanitized filename, owner-scoped idempotency key, counts and validation errors. Uploaded CSV bytes are not retained.
- Import is atomic: invalid rows or changed content behind an existing external reference reject the entire batch and insert zero transaction rows.
- Exact repeated provider references in the same lifecycle state are skipped. Similar transactions without an external reference are retained and flagged as possible duplicates, not silently discarded.
- Provider lifecycle changes are reconciled monotonically for the same financial fingerprint: `PENDING -> POSTED|REVERSED|VOID` and `POSTED -> REVERSED|VOID`. Terminal `REVERSED`/`VOID` records cannot be reactivated. Batch `updated_count` and per-transaction audit events distinguish status reconciliation from inserts and duplicates; application checks plus SQLite/PostgreSQL database guards enforce financial-fact immutability and the monotonic transition graph.
- Cashflow includes only `POSTED`: `INCOME` credit adds income; `EXPENSE` debit adds gross expense; `REFUND` credit offsets expense, not income; `TRANSFER` and `IGNORE` do not affect income/expense. If CSV treatment is missing, default to `IGNORE` rather than assuming credits are income or debits are expenses. `amount_inr` is rejected for non-INR accounts. Pending/reversed/void are excluded. Output names its ratio `net_cashflow_to_income_percent`, not savings.
- Verified account/transaction/import/obligation APIs return 404 for non-owner lookups. Household membership does not grant transaction access.
- Local-only synthetic seeder loads one fixture persona into an existing active, verified local user; it refuses production and never creates a fake login identity.

## 3. API routes added in Iteration 02

- `POST /api/v1/financial/accounts`
- `GET /api/v1/financial/accounts`
- `POST /api/v1/financial/accounts/{account_id}/imports/csv` (`Idempotency-Key` required)
- `GET /api/v1/financial/imports/{batch_id}`
- `GET /api/v1/financial/accounts/{account_id}/transactions?limit=&offset=`
- `GET /api/v1/financial/cashflow?period_start=&period_end=&currency=`
- `POST /api/v1/financial/obligations`
- `GET /api/v1/financial/obligations`

Every route requires verified authentication. These are owner-personal endpoints. No household or Commons data-sharing read path is implemented.

## 4. Iteration 02 verification record

Local checks on the Iteration 02 source tree:

- `PYTHONPATH=src pytest -q`: **56 passed**.
- `python -m compileall -q src tests migrations scripts`: passed.
- SQLite Alembic `upgrade head -> downgrade base -> upgrade head`: passed, including the transaction financial-fact immutability and status-transition guard create/drop/recreate path.
- Direct SQLite database test confirmed a `REVERSED -> POSTED` update is rejected by the migration-equivalent DB trigger. Application test confirmed a provider import also rejects reactivation and leaves the row terminal.
- PostgreSQL offline SQL generation succeeded and contains the transaction financial-fact immutability/status-transition guard function and trigger. A live PostgreSQL 16 execution of Iteration 02's new trigger is still pending its own CI after push.
- Synthetic dataset independent validator: passed against committed v1.0.0 corpus.
- Final re-run on 2026-11-04: `PYTHONPATH=src pytest -q` **56 passed**; Python compileall passed; fresh SQLite migration upgrade/downgrade/re-upgrade passed; PostgreSQL offline SQL contains the new financial transaction guard function/trigger.
- Final synthetic seeder smoke: first run inserted 91 transactions / created 2 accounts and 5 obligations; second run inserted 0 / updated 0, replayed 2 batches and reused 5 obligations; stable counts remained 2 accounts, 91 transactions, 5 obligations and 2 batches.
- Synthetic dataset final independent validation: all 42 table PK/FK checks, business-rule validations, export parity, multimodal hashes and SQLite integrity passed across 17,425 rows.
- Local SQLite integration smoke: seeded `CUS00001` into an existing verified local test user; first run created 2 accounts, inserted 91 transactions and created 5 obligations; second run reused 2 accounts, reported 2 replayed import batches / 91 replayed historical rows (not new inserts), and reused 5 obligations. Final counts remained 2 accounts, 91 transactions, 5 obligations and 2 batches.
- `git diff --check`: passed on the prepared source tree before final packaging; rerun in the user's Git checkout before commit.
- Ruff: the isolated execution environment does not have the Ruff executable and package download was unavailable, so the new Iteration 02 Ruff result is **unverified**. Do not infer the merged Iteration 01 CI result covers these new files; the owner must run local Ruff and the new branch CI must pass.
- PostgreSQL 16 live migration verification was passed for merged Iteration 01 on GitHub main. The new Iteration 02 migration has only been tested on SQLite and compiled to PostgreSQL offline SQL locally; it needs its own PostgreSQL CI run after push.

## 5. Explicitly not implemented

No live bank/Account Aggregator connection, bank credential collection, payment initiation, automatic debit/autopay mandate, opening-balance reconciliation, FX service, budgets/goals/forecast, bill/document vault, Guardian claim submission, official benefits catalogue, opportunity marketplace integration, resource exchange, crisis engine, enterprise commerce integration, Commons aggregation runtime, offer optimizer, VIVC verification, partner commission/payout, RAG, graph runtime, durable agent mission/checkpoint service, Meta model gateway or production deployment exists yet. The synthetic fixture corpus for those capabilities is a test/demo dataset only.

## 6. Release/security gaps for the financial data plane

- Run Iteration 02 CI on Python 3.12/3.13 and PostgreSQL 16; inspect the new composite foreign keys, partial unique index, transaction immutability/status guard and rollback on both databases; CI also revalidates all synthetic dataset exports/documents.
- Add concurrency tests for two simultaneous uploads with the same idempotency key/provider reference; unique constraints are present but race behavior needs service-backed tests.
- Add streaming multipart/file integration only if required; current CSV endpoint is raw `text/csv` body.
- Add a user-reviewed reclassification API for rows imported as `IGNORE`; do not infer income/expense from direction alone.
- Add explicit correction/compensating-event workflows for changing financial facts; only the narrow provider lifecycle transition is implemented now.
- Add pagination total/next cursor and filtering/index benchmarks for large histories.
- Add retention, export/erasure policy, field-level encryption/key management, request/IP rate controls, malware scanning for future documents, privacy/security review and penetration testing before production.
- Validate ISO 4217 currency registry from an authoritative source before expanding the curated list.
- Build a bank integration only through a supported provider with the correct user consent and regulatory roles; never collect raw bank passwords.

## 7. Next iteration direction

Iteration 03 should deliver an evidence-grounded **Personal Power / Guardian** vertical slice using the now-persisted user-owned financial data plus synthetic invoice documents. Its workflow should be: user-authorized upload -> document validation/provenance -> model-assisted extraction with evidence spans -> deterministic numeric comparison -> risk/uncertainty explanation -> draft action -> explicit human approval -> auditable outcome state. No complaint, payment, cancellation or provider contact is executed without a real supported integration and user approval. Meta AI should be integrated because it materially performs extraction/reasoning, not decoratively.

The longer-term eight pillars and Commons killer move remain recorded in `PROJECT_MEMORY.md`, `FEATURE_CATALOG.md` and `docs/DEMO_PLAYBOOK.md`. Do not try to ship all pillars as disconnected stubs in one iteration.

## 8. Status update rule

At each future iteration, re-read live repository metadata, latest `main` HEAD, active feature branch, CI status and the four core memory documents before modifying files. Update this document, `CODEBASE_MAP.md`, `FEATURE_CATALOG.md`, the iteration record and the relevant decisions in the same delivery. Local commits/archives are never described as pushed until GitHub confirms the remote write.
