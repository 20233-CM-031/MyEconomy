# Iteration 01 — File-level Change Manifest

**Branch:** `iteration/01-trust-foundation`
**Date:** 2026-11-03
**Scope:** identity, email verification, household membership/invitations, purpose-bound consent, append-only audit and CI database verification.

This manifest describes every file changed or added in the Iteration 01 delivery relative to the local Iteration 00/memory-map baseline. The live GitHub `main` branch was inspected at `6a1b57e66536d54fe4cc96f05924d5baf868593a`. The remote is an Iteration 00 source tree. Its expanded `.gitignore` and `pythonpath = ["src"]` pytest setting are preserved in this iteration. One remote-specific difference matters: `.github/workflows/ci.yml` is absent on remote `main`; this delivery adds it. Remote write access returned HTTP 403, so the delivery is local and must be pushed by an authenticated Git client.

## Added files

| Repository path | Responsibility / important contents | Dependencies / verification |
|---|---|---|
| `alembic.ini` | Alembic configuration and migration script location. | SQLAlchemy/Alembic; exercised through SQLite migrations and PostgreSQL offline SQL generation. |
| `migrations/env.py` | Loads SQLAlchemy metadata, reads `DATABASE_URL`, applies online/offline migrations and enables SQLite foreign keys. | `infrastructure.models.Base`; SQLite upgrade/downgrade/re-upgrade passed. |
| `migrations/script.py.mako` | Template for future versioned migrations. | Alembic. |
| `migrations/versions/8ec10b31a771_identity_consent_and_household_trust_.py` | Creates users, sessions, households, membership, invitations, consent grants and audit events; adds audit immutability triggers. | SQLite execution passed; PostgreSQL offline SQL generated; PostgreSQL service CI added but not yet run. |
| `migrations/versions/3b2e7f4a9c10_email_verification_challenges.py` | Adds one-time email challenge table, token digest uniqueness and one-pending-challenge partial index. | SQLite execution passed; PostgreSQL offline SQL generated. |
| `src/myeconomy/api/dependencies.py` | Bearer-session resolution and verified-account dependency. | Application identity resolver; exercised by identity/household/consent tests. |
| `src/myeconomy/api/identity_schemas.py` | Strict Pydantic request/response contracts for identity, verification, households, invitations, memberships and consents. | Domain consent enums; validation tested by API tests. |
| `src/myeconomy/api/identity_routes.py` | HTTP endpoints for account lifecycle, verification, household actions and consent lifecycle. | Application use cases + infrastructure adapters; 36 core tests and live HTTP smoke, plus 5 email-adapter tests. |
| `src/myeconomy/application/audit.py` | Central append-only audit event writer; prohibits putting secrets/raw documents into event details by contract. | SQLAlchemy `AuditEvent`; ORM and DB-level immutability. |
| `src/myeconomy/application/identity.py` | Account registration, normalized email, password verification, session lifecycle, email challenge issuance/verification. | Argon2/security adapter, DB models, audit writer. |
| `src/myeconomy/application/households.py` | Household creation/listing, owner-only invitations, verified email-bound acceptance, revocation and member listing. | Consent-independent membership layer, token security and audit. |
| `src/myeconomy/application/consents.py` | Consent grant creation/listing/revocation, expiry calculation, exact-scope matching and enforcement helper. | Domain allowlists, membership check, persistence and audit. |
| `src/myeconomy/domain/consent.py` | Framework-independent consent vocabulary, purpose/category allowlists, recipient requirements and versioned text. | No persistence/API dependency; tested through consent cases. |
| `src/myeconomy/domain/errors.py` | Stable application/domain error types mapped to safe HTTP status and codes. | `main.py` exception handler. |
| `src/myeconomy/infrastructure/database.py` | Database engine, environment loading, SQLite foreign-key enablement and request-scoped sessions. | SQLAlchemy, dotenv, psycopg for PostgreSQL. |
| `src/myeconomy/infrastructure/models.py` | SQLAlchemy persistence entities, unique/partial indexes, check constraints and ORM append-only audit hooks. | SQLAlchemy; migration parity must be maintained. |
| `src/myeconomy/infrastructure/security.py` | Argon2 password hashing, dummy hash path, 256-bit opaque tokens and digest storage. | `argon2-cffi`, `secrets`, `hashlib`; tested via identity flows. |
| `src/myeconomy/infrastructure/email_delivery.py` | Development-only log adapter and environment-configured SMTP adapter with STARTTLS. | `smtplib`; unit tested with fake SMTP, not tested against live provider. |
| `scripts/verify_postgres_audit.py` | CI-only synthetic insert/update/delete probe confirming PostgreSQL audit trigger immutability. | PostgreSQL DSN; added to CI job, first GitHub run pending. |
| `tests/conftest.py` | Isolated SQLite fixture, migration marker, audit triggers, DB dependency override and verification-email capture. | Pytest/FastAPI/SQLAlchemy. |
| `tests/test_identity.py` | Registration, password/session hashing, generic auth failures, expiry, email verification, replay/cooldown and verified-account gates. | `pytest`; 36-test suite before adding email-adapter tests. |
| `tests/test_households.py` | Owner role, invitation email binding, expiry/replay/revocation, member visibility and non-implied consent. | `pytest` and isolated SQLite DB. |
| `tests/test_consents.py` | Scope allowlists, membership, version/expiry, cross-user denial, revocation and audit immutability. | `pytest` and isolated SQLite DB. |
| `tests/test_email_delivery.py` | Development-only log policy, production refusal, missing SMTP config, STARTTLS/message construction and secret-safe logging. | Fake SMTP; does not replace live SMTP-provider verification. |
| `docs/HACKATHON_SCORECARD.md` | User-supplied scoring rubric, feature impact story, Meta model strategy, bonus targets, demo evidence, current gap status and deadline conversion. | Official source links are embedded; bonus conditions are labelled user-provided pending rules verification. |
| `docs/THREAT_MODEL.md` | Security assets, actors, trust boundaries, implemented controls, residual risks and production blockers. | Updated alongside each trust/security change. |
| `docs/decisions/ADR-0002-identity-consent-sessions.md` | Rationale for Argon2id, opaque sessions, email proof, separation of household membership/consent, and audit. | Decision record; future changes should add an ADR rather than silently reverse it. |
| `docs/iterations/ITERATION-01.md` | User stories, scope, invariants, schema, API, acceptance evidence and limitations. | Iteration completion source. |
| `docs/iterations/ITERATION-01-FILE-MANIFEST.md` | This exhaustive path/responsibility map. | Must be updated when files change during the iteration. |

## Modified files

| Repository path | What changed | Why / verification |
|---|---|---|
| `.env.example` | Added app environment, development email backend, database URL and SMTP variables. | Safe local configuration; production default refuses log mail. |
| `.github/workflows/ci.yml` | Adds a Python 3.12/3.13 test matrix, Ruff, SQLite migration roundtrip and PostgreSQL 16 migration/trigger job. | This file existed on the local Iteration 00 branch but was absent from confirmed remote `main`; on GitHub it is a new file. CI has not yet run remotely. |
| `.gitignore` | Preserved the fuller remote Python template, `.env.*` ignore with `.env.example` exception, and added SQLite/database exclusions. | Avoid committing secrets/runtime artefacts without losing remote ignore rules. |
| `AGENTS.md` | Added product context, engineering constraints, iteration and delivery rules. | Durable AI/contributor operating contract. |
| `Dockerfile` | Containerized the API runtime. | Repeatable local/CI execution; production deployment still needs environment hardening. |
| `Makefile` | Added repeatable development/test/migration commands. | Reduce command drift. |
| `README.md` | Added setup, run/test instructions, current API list, security boundaries and documentation map. | Entry point for contributors and judges; reconciled with latest remote README content read during this session. |
| `docs/AI_COLLABORATION_PROTOCOL.md` | Made GitHub inspection, memory refresh, per-file manifest and no-false-push rules mandatory. | Preserve project continuity across AI sessions. |
| `docs/ARCHITECTURE.md` | Expanded modular-monolith, trust-boundary, persistence, domain and future AI/network architecture. | Keep implemented structure distinct from target vision. |
| `docs/CODEBASE_MAP.md` | Added exact module symbols, route/use-case flow, migrations, tests and PostgreSQL CI script. | Deep code/context navigation. |
| `docs/ENGINEERING_STANDARDS.md` | Tightened money, AI, security, test and workflow standards. | Definition of Done. |
| `docs/FEATURE_CATALOG.md` | Updated identity, email verification, household, consent and audit status; retained future capabilities as Designed/Not started. | Avoid overstating product completeness. |
| `docs/ITERATION_PLAN.md` | Added trust iteration and documented later financial-data, Personal Power, feature and agent/model iterations. | Sequencing and acceptance criteria. |
| `docs/PROJECT_MEMORY.md` | Reconciled the full personal-first/Commons vision, eight pillars, model safety and current implementation. | Repository as durable project memory. |
| `docs/PROJECT_STATUS.md` | Updated remote/local state, implemented scope, routes, verification, current blockers and next steps. | Single factual status ledger. |
| `pyproject.toml` | Added SQLAlchemy/Alembic/Argon2/email/PostgreSQL dependencies, FastAPI dependency-injection Ruff exception and retained remote `pythonpath = ["src"]`. | Reproducible dependency contract and preservation of the remote test-import setting. |
| `src/myeconomy/main.py` | Registered trust router and added stable application error handling plus DB/schema-aware readiness. | Composition root and operational readiness. |
| `tests/test_api.py` | Updated health/readiness tests for DB/schema and retained cashflow API coverage. | Protect service health semantics. |
| `tests/test_cashflow_domain.py` | Expanded boundary tests for supported currency precision and categories. | Preserve Iteration 00 calculations while adding identity persistence. |

## Runtime call paths

- Registration: `POST /auth/register` → `register_user` → `create_session` → `issue_email_verification_challenge` → `send_verification_email`.
- Email proof: `POST /auth/verify-email` → digest lookup → expiry/replay/revocation checks → `User.email_verified = true` → challenge consumed.
- Household: verified owner → `create_household` → owner membership; then invitation creation → invited account email proof → single-use acceptance.
- Consent: verified subject → current terms → exact purpose/category/recipient scope → grant persisted and audited; revocation makes future exact-scope checks return false.
- Data access policy: future reader must call `require_active_consent` inside the same transaction as the protected read. The current check endpoint is informational only.

## Rollback and migration notes

- Database schema is versioned by Alembic. Roll back using `alembic downgrade <revision>` only after reviewing data-loss implications; dropping the initial Iteration 01 migration removes all identity/household/consent/audit tables.
- Application rollback should deploy a version compatible with the previous migration revision before running destructive downgrade.
- Do not edit an already-applied migration; create a new forward migration.
- No real user data should be in the demo DB. Use synthetic accounts and reset the local database between demos if appropriate.
