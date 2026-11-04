# MyEconomy — Personal Economic Agency & Collective Opportunity Intelligence

> Product brand name: **not selected**. `MyEconomy` is the repository and internal project name.

The product vision is to make each person stronger from Day One through a private AI representative that helps protect their interests, recover value, discover opportunities, access benefits, develop income and operate a small enterprise. With explicit, purpose-specific consent, personal agents can participate in a privacy-preserving Collective Economic Intelligence Network that turns shared demand and underused resources into collective opportunity.

**Product principle:** Intelligence for the individual. Power for everyone.

## Current implementation status

This repository is being built as a carefully engineered modular monolith. Iteration 00 contains deterministic cashflow analysis. Iteration 01 adds persisted identity/session management, household invitations and membership boundaries, scoped consent grants, revocation, and append-only audit events. Iteration 02 adds owner-scoped financial accounts, transaction statement import with provenance/idempotency, persisted transaction ledger, recurring obligations and cashflow analysis over posted records. Provider lifecycle changes (`PENDING` to `POSTED`/`REVERSED`/`VOID`, `POSTED` to `REVERSED`/`VOID`) are audited and database-enforced; unclassified CSV rows default to `IGNORE` rather than guessing from debit/credit direction.

Implemented functionality is described in `docs/PROJECT_STATUS.md`. The complete future vision is not yet implemented. No bank connection, payments, sponsor/merchant integrations, live Commons marketplace, production agent, RAG engine or Meta model integration is claimed as working yet.

## Engineering memory — read first

1. [`AGENTS.md`](AGENTS.md) — mandatory instructions for AI assistants and contributors.
2. [`docs/PROJECT_MEMORY.md`](docs/PROJECT_MEMORY.md) — durable product and system memory.
3. [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) — factual current state and blockers.
4. [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md) — code ownership and runtime flow.
5. [`docs/FEATURE_CATALOG.md`](docs/FEATURE_CATALOG.md) — capability status ledger.
6. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/ENGINEERING_STANDARDS.md`](docs/ENGINEERING_STANDARDS.md) — design and quality rules.
7. [`docs/HACKATHON_SCORECARD.md`](docs/HACKATHON_SCORECARD.md) — strategy against the judging criteria supplied by the team and current official references.
8. [`docs/iterations/`](docs/iterations/) and [`docs/decisions/`](docs/decisions/) — iteration evidence and architecture decisions.

## Requirements

- Python 3.12 or 3.13
- SQLite for local development, or PostgreSQL for shared/staging/production deployments

## Local development

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
pytest -q
ruff check src tests migrations
ruff format --check src tests migrations
uvicorn myeconomy.main:app --reload
```

The app is available at `http://127.0.0.1:8000`; OpenAPI is at `/docs`.

For PostgreSQL, set `DATABASE_URL` to a `postgresql+psycopg://...` URL before running migrations. Apply migrations as a controlled release step, not concurrently from every application replica.

## API surface

- `GET /health/live` — process liveness.
- `GET /health/ready` — database connection and migration-table readiness.
- `POST /api/v1/cashflow/analyze` — deterministic calculation over caller-supplied data; no persistence.
- `POST /api/v1/financial/accounts`, `GET /api/v1/financial/accounts` — create/list only the authenticated user's financial account metadata.
- `POST /api/v1/financial/accounts/{account_id}/imports/csv` — bounded, strict CSV import with an `Idempotency-Key`; source file bytes are not retained. Response distinguishes inserted, lifecycle-updated, duplicate and potential-duplicate rows.
- `GET /api/v1/financial/imports/{batch_id}` — owner-scoped import provenance and validation result.
- `GET /api/v1/financial/accounts/{account_id}/transactions` — owner-scoped, paginated ledger.
- `GET /api/v1/financial/cashflow?period_start=YYYY-MM-DD&period_end=YYYY-MM-DD&currency=INR` — persisted cashflow for one currency.
- `POST /api/v1/financial/obligations`, `GET /api/v1/financial/obligations` — recurring obligation schedule records.
- `POST /api/v1/auth/register`, `POST /api/v1/auth/verify-email`, `POST /api/v1/auth/verification/resend`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me` — account, email verification and opaque-session lifecycle.
- `POST /api/v1/households`, `GET /api/v1/households` — create and list the current user's households after email verification.
- `POST /api/v1/households/{id}/invitations`, `POST /api/v1/household-invitations/accept`, `POST /api/v1/household-invitations/{id}/revoke`, `GET /api/v1/households/{id}/members` — invitation-acceptance membership flow.
- `GET /api/v1/consents/terms`, `POST /api/v1/consents`, `GET /api/v1/consents`, `POST /api/v1/consents/{id}/revoke`, `GET /api/v1/consents/check` — versioned purpose/category/recipient-bound consent.

Household membership does not grant access to a member's personal or financial records. Financial account and transaction endpoints are scoped to the authenticated account owner; Commons sharing is not yet implemented. Each person must separately grant the necessary consent. The check endpoint is informational; future data services must call `require_active_consent` inside the same transaction as the data access. See `docs/THREAT_MODEL.md` for residual risks and `docs/HACKATHON_SCORECARD.md` for the judging strategy.

## Security and current limitations

- Passwords are hashed using Argon2id via `argon2-cffi`.
- Sessions are random opaque bearer tokens; only SHA-256 token digests are stored. Default session lifetime is 12 hours.
- Consent expires by default after 90 days and cannot exceed 365 days in this iteration; revocation is immediate.
- Audit events are append-only at the ORM and database-trigger layer.
- Household and consent operations require verified email control. Local `.env.example` uses a development-only log backend that prints the one-time verification token; never set `EMAIL_BACKEND=log` outside `APP_ENV=development` or `test`. SMTP adapter exists but has not been verified with a live provider.
- Household invite tokens are returned once by the API; email delivery is not implemented for invitations and response explicitly says `manual_share_required`.
- Password reset, MFA/passkeys, login throttling, distributed rate limiting, account export/erasure, managed secrets, encryption-at-rest/KMS, production TLS/headers and independent penetration testing remain release blockers.
- No bank/merchant/provider calls are made. No personal information is sent to Meta models. Any future AI integration must use minimized data, user-consistent policy, and the appropriate Meta service tier; Contributor mode must never receive personal or confidential end-user data.

## Contribution workflow

Use `iteration/<number>-<scope>` branches, conventional commits, tests and documentation updates. Every completed iteration must update the project status, codebase map, feature catalog, project memory and iteration evidence. See `AGENTS.md`.

Iteration 01 detailed implementation and file manifest: `docs/iterations/ITERATION-01.md` and `docs/iterations/ITERATION-01-FILE-MANIFEST.md`. Iteration 02 financial data contract and delivery manifest: `docs/FINANCIAL_DATA_CONTRACT.md`, `docs/iterations/ITERATION-02.md` and `docs/iterations/ITERATION-02-FILE-MANIFEST.md`.

## Synthetic end-to-end demo data

A deterministic India-oriented synthetic dataset now lives at `demo_data/synthetic_v1/`. It contains linked financial, household, bill, loan, consent, benefits, skills, opportunity, Commons, Guardian, crisis, risk, enterprise and agent-workflow fixtures in CSV, JSON, JSONL, PostgreSQL SQL, SQLite and source-document formats.

Start with:

- `docs/SYNTHETIC_DEMO_DATASET.md` — dataset architecture, format and safety boundaries.
- `docs/DEMO_PLAYBOOK.md` — exact scenario walkthroughs, including one-user Day-One value and a five-user Commons quorum.
- `demo_data/synthetic_v1/README.md` — generator, formats and reproduction instructions.
- `demo_data/synthetic_v1/metadata/validation_report.json` and `independent_validation_report.json` — generated validation evidence.

**Critical:** the records are entirely synthetic. They are for local testing, demos, model evaluation and integration contracts only. They must never be represented as real users, actual benefits, real provider bids, real financial outcomes or completed transactions.

## Synthetic end-to-end demo corpus

The complete synthetic relational fixture corpus is under `demo_data/synthetic_v1/`. It includes 42 entity tables and 17,425 rows, exports in CSV/JSON/JSONL/PostgreSQL SQL/SQLite, synthetic invoice HTML/PDF/PNG source documents, scenario payloads, data dictionary, business rules and an independent validator.

Read `docs/SYNTHETIC_DEMO_DATASET.md`, `docs/DEMO_PLAYBOOK.md` and `demo_data/synthetic_v1/DEMO_PLAYBOOK.md` before using it. Every record is synthetic, all provider/benefit/order/payment outcomes are simulated, and synthetic value events must not be counted as real user impact.


## Iteration 02 — Financial Data Plane v1

Iteration 02 adds owner-scoped account metadata, bounded CSV statement imports, an integer-minor-unit transaction ledger, import idempotency/provenance, provider status reconciliation, posted-only cashflow reads and recurring obligations. It uses a conservative `IGNORE` treatment when transaction classification is missing. Provider-status changes are monotonic and audited; financial facts are guarded as immutable in SQLite and PostgreSQL. See `docs/FINANCIAL_DATA_CONTRACT.md` and `docs/iterations/ITERATION-02.md`.

**Limitations:** no live bank/Account Aggregator integration, payment initiation, automated debit, FX conversion, budget/goal engine, Guardian action submission, agent runtime or Meta model gateway is implemented in this iteration. The synthetic data under `demo_data/synthetic_v1/` is for local test/demo use only.
