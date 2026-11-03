# Codebase Map — Actual Source and Runtime Flow

**Map version:** 2.0 · **Last reconciled:** 2026-11-03
This document describes files and symbols that exist in the repository now. Future architecture belongs in `ARCHITECTURE.md` and `PROJECT_MEMORY.md` until implemented.

## 1. Layer boundaries

`HTTP API -> application use cases -> domain rules` and `application -> infrastructure adapters / persistence`.

- `domain/` is framework-independent: no FastAPI, SQLAlchemy session, LLM SDK or provider API.
- `application/` owns use-case orchestration, transaction boundaries and audit calls.
- `infrastructure/` owns SQLAlchemy, security primitives, environment/database setup and email transport.
- `api/` owns HTTP schema, auth dependencies, route mapping and response models.
- `main.py` is the composition root.

## 2. Application entry and composition

### `src/myeconomy/main.py`
- `create_app()` constructs FastAPI, installs stable `ApplicationError` handling, registers cashflow and identity/trust routers, and exposes liveness/readiness routes.
- `GET /health/live` confirms process liveness only.
- `GET /health/ready` executes a DB probe and checks `alembic_version`; readiness is 503 when schema is missing/unavailable.
- `app = create_app()` is the ASGI import target.

## 3. Domain layer

### `src/myeconomy/domain/money.py`
- `MoneyInputError`: invalid monetary representation.
- `currency_exponent(currency)`: retrieves supported currency precision from the curated registry.
- `quantize_amount(...)`, `quantize_total(...)`: quantize with `Decimal` and the currency exponent. No FX conversion.

### `src/myeconomy/domain/cashflow.py`
- `CashflowEntry`, `CategoryTotal`, `CashflowSummary`: immutable domain records.
- `_validate_entries(...)`: validates period bounds, positive finite amounts, supported currency precision and normalized category.
- `analyze_cashflow(...)`: pure analysis function. Computes income, expense, net cashflow, essential/discretionary amounts, category totals and net-cashflow/income ratio.

### `src/myeconomy/domain/consent.py`
- `ConsentPurpose`, `DataCategory`, `RecipientType`: typed vocabulary for authorized purposes, data classes and recipient classes.
- `_ALLOWED_CATEGORIES`: purpose-to-category allowlist; Commons/research exclude raw transactions, contact and support documents.
- `_REQUIRED_RECIPIENT_TYPES`: deterministic required recipient kind per purpose.
- `validate_consent_scope(...)`: rejects wrong recipient type, empty/duplicate categories, disallowed categories, invalid recipient identifiers and Commons target other than `commons`.
- `ConsentTerms`, `_CONSENT_TERMS`: user-facing versioned summaries and revocation notes.
- `get_consent_terms`, `list_consent_terms`, `allowed_categories_for_purpose`, `required_recipient_type`: policy lookups.

### `src/myeconomy/domain/errors.py`
Stable application error classes and safe public codes/status: conflict (409), authentication (401), not found (404), authorization (403), invalid consent scope (422), consent required (403), invalid verification (400), rate limited (429), service unavailable (503).

## 4. Application layer

### `src/myeconomy/application/cashflow.py`
- `run_cashflow_analysis(...)`: adapts API request entries into domain records and returns the pure summary.

### `src/myeconomy/application/identity.py`
- `normalize_email(...)`: trim + casefold email for account matching.
- `register_user(...)`: validate name, Argon2-hash password, persist user, append registration audit event.
- `authenticate_user(...)`: generic failure path, dummy-hash behavior from security adapter, optional password hash rehash, audit and commit.
- `create_session(...)`: generate opaque token, persist only digest, 12-hour expiry, audit and commit.
- `resolve_session(...)`: hash bearer token, reject missing/revoked/expired/inactive, update last-used timestamp.
- `revoke_session(...)`: revoke one user's session and append audit event.
- `issue_email_verification_challenge(...)`: issue one-time token, revoke previous pending token, 24-hour expiry, 60-second resend cooldown and audit.
- `verify_email_address(...)`: validate digest, expiry, single-use and user state; mark email verified, revoke other active challenges and audit.

### `src/myeconomy/application/households.py`
- `require_household_membership(...)`: resource-level membership guard; hides household existence from nonmembers.
- `create_household(...)`: create household and owner membership atomically with audit.
- `list_households(...)`: lists only memberships for current user.
- `create_household_invitation(...)`: owner-only; normalized email, duplicate/active checks, 72-hour token, hashed token storage and audit.
- `accept_household_invitation(...)`: single-use, unexpired, nonrevoked token; compares verified account email and creates member role.
- `revoke_household_invitation(...)`: owner-only invitation revocation.
- `list_household_members(...)`: member-only limited membership metadata; records audit event. API serializer intentionally omits email.

### `src/myeconomy/application/consents.py`
- `effective_status(...)`: active/revoked/expired derived state.
- `create_consent(...)`: checks current terms version, purpose/category/recipient policy, bounded expiry and household membership when applicable; persists grant and audit.
- `list_consents(...)`: only the current user's grants.
- `revoke_consent(...)`: owner-scoped revocation; idempotent.
- `has_active_consent(...)`: exact match of subject, purpose, category, recipient and nonexpired active grant.
- `require_active_consent(...)`: raises if scope missing. Every future protected data service must call this inside the same transaction as the protected read/write. It is not automatically applied to nonexistent future services yet.

### `src/myeconomy/application/audit.py`
- `record_audit_event(...)`: central append-only event writer; call sites must never send raw passwords, tokens, documents or unrelated PII.

## 5. Infrastructure layer

### `src/myeconomy/infrastructure/database.py`
- Loads `.env`, builds SQLAlchemy engine from `DATABASE_URL`, enables SQLite foreign keys, and provides request-scoped `get_db()` sessions.
- SQLite is the local default; PostgreSQL uses `psycopg`.

### `src/myeconomy/infrastructure/models.py`
SQLAlchemy `Base` tables:
- `User`: normalized email, password hash, display name, email verification flag, active flag.
- `AuthSession`: user FK, token digest, created/expiry/revocation/last-used timestamps.
- `EmailVerificationChallenge`: user FK, token digest, created/expiry/consumed/revoked fields; partial unique active challenge per user.
- `Household`: name, creator, creation timestamp.
- `HouseholdMembership`: unique household/user pair and constrained role.
- `HouseholdInvitation`: recipient email, token digest, inviter, expiry/accept/revoke state; partial unique active invitation per household/email.
- `ConsentGrant`: subject, purpose, JSON categories, recipient type/id, terms version, status and lifecycle timestamps.
- `AuditEvent`: pseudonymous actor/household IDs, action, subject, JSON details and timestamp; ORM hooks reject update/delete.

### `src/myeconomy/infrastructure/security.py`
- `hash_password`, `verify_password`, `password_hash_needs_rehash`: Argon2 password primitives and dummy hash path.
- `issue_session_token`: high-entropy opaque token.
- `hash_session_token`: SHA-256 digest for high-entropy opaque tokens/challenges.

### `src/myeconomy/infrastructure/email_delivery.py`
- `EmailDeliveryFailure`: transport/configuration error.
- `send_verification_email(...)`: development-only log backend (rejects in non-development/test) or SMTP sender using environment-configured credentials; logs no SMTP secrets. SMTP must be verified with a live provider before production.

## 6. API layer and public endpoints

### `src/myeconomy/api/dependencies.py`
- `AuthContext`: verified session/user pair.
- `require_authentication(...)`: parses bearer token and resolves session.
- `require_verified_authentication(...)`: rejects unverified accounts before household/consent operations.

### `src/myeconomy/api/identity_schemas.py`
Pydantic v2 schemas for register/login, email verification, user/session response, household and invitation payloads, member metadata, consent grant/check/terms. `extra='forbid'` is used on input payloads; passwords use `SecretStr`.

### `src/myeconomy/api/identity_routes.py`
- Registration/login/logout/me and email verify/resend.
- Household create/list, invite/accept/revoke and member list.
- Public versioned consent terms; authenticated consent grant/list/revoke/check.
- Maps application services and models to response schemas; trust routes require verified identity except terms.

### `src/myeconomy/api/routes.py`, `schemas.py`
Cashflow request schemas and `/api/v1/cashflow/analyze` route.

## 7. Database migrations

- `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`: Alembic config and metadata environment.
- `migrations/versions/8ec10b31a771_identity_consent_and_household_trust_.py`: initial identity/session/household/invitation/consent/audit schema and immutable audit triggers.
- `migrations/versions/3b2e7f4a9c10_email_verification_challenges.py`: one-time verification challenge table and partial unique active-challenge index.

Run `alembic upgrade head` as a controlled release step. Do not run migrations concurrently from each production app replica.

## 8. Operational verification scripts

### `scripts/verify_postgres_audit.py`
- Runs only when `DATABASE_URL` targets PostgreSQL.
- Inserts one synthetic CI probe event, verifies database-trigger UPDATE and DELETE rejection, then confirms the original event remains unchanged.
- The CI PostgreSQL job runs it after `alembic upgrade head`; it is not a production endpoint or application runtime feature.

## 9. Tests

- `tests/conftest.py`: isolated in-memory SQLite DB, migration marker, audit triggers, dependency override and captured verification-email adapter.
- `tests/test_cashflow_domain.py`: deterministic money/cashflow rules.
- `tests/test_api.py`: cashflow API validation and health/readiness.
- `tests/test_identity.py`: password/session hashes, generic login failures, protected routes, logout, expiry, verification, replay and resend cooldown.
- `tests/test_email_delivery.py`: explicit development-only log mode, production refusal, SMTP config/STARTTLS/message contract and secret-safe logging.
- `tests/test_households.py`: invitation binding, role checks, replay/expiry/revoke, cross-account isolation, membership privacy and no implied consent.
- `tests/test_consents.py`: purpose/category restrictions, revocation, membership prerequisite, expiry, ownership, terms and audit immutability.

## 10. Runtime path examples

### Register and verify

`POST /auth/register` -> `register_user` -> `create_session` -> `issue_email_verification_challenge` -> `send_verification_email` -> client receives session and verification message -> `POST /auth/verify-email` -> `verify_email_address` -> `User.email_verified = true`.

### Household membership

Verified owner -> `create_household` -> owner membership -> create invitation -> invitee registers/logs in and verifies email -> accept one-time invitation -> membership created. No financial records are read or shared by this flow.

### Consent lifecycle

Verified user -> read current terms -> submit exact version/purpose/categories/recipient/confirmation -> `create_consent` validates domain allowlists and expiry -> audit. Revocation flips status and audit; `has_active_consent` denies future checks. Future data readers must enforce in the same transaction.

### Current cashflow

HTTP request -> Pydantic validation -> `run_cashflow_analysis` -> pure `analyze_cashflow` domain -> JSON response. No personal record is stored.

## 11. Known boundaries

No bank connector, transaction persistence, budget goals/forecast, benefit/provider source, claim workflow, agent runtime, RAG/vector/graph engine, Commons matcher, payments, sponsor integration or Meta model gateway exists in code today. These belong to later iterations and must never be described as implemented yet.

## 5. Synthetic demo data layer (2026-11-03)

`demo_data/synthetic_v1/` is a data/fixture layer, not a runtime service. It contains the deterministic generator and overlay scripts; 42 related CSV/JSON/JSONL entity exports; PostgreSQL schema/seed; SQLite database; synthetic invoice/offer source documents; API scenario JSON; schema catalog, data dictionary, business rules, regulatory matrix and validation reports. See `docs/SYNTHETIC_DEMO_DATASET.md` and `docs/DEMO_PLAYBOOK.md` before changing it.

The canonical reproduction path is: generate base records -> apply demo scenario overrides -> rebuild SQLite -> run independent validator. When data changes, regenerate all row exports and SQL/SQLite representations together. Never edit only one serialization. All rows remain `SYNTHETIC_FIXTURE`; no dataset fixture may be loaded into a real partner, payment or production customer environment.
