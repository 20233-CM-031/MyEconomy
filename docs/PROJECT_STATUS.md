# Project Status

**Last reconciled:** 2026-11-03
**Repository:** `20233-CM-031/MyEconomy`
**Remote default branch observed:** `main`
**Local branch:** `iteration/01-trust-foundation`
**Latest implementation commit:** `8b7523f` (`feat: add identity and consent trust foundation`) — local only, not pushed.
**Brand:** Not selected (`MyEconomy` remains repository/internal name).

## 1. Remote and local repository state

The live GitHub repository was re-read during this iteration. The default branch is `main`; its current head is `6a1b57e66536d54fe4cc96f05924d5baf868593a` (`feat: initialize MyEconomy iteration 00 foundation with memory and cashflow slice`). The remote contains the complete Iteration 00 source tree and memory documents, not merely a README. The inspected cashflow domain and API source contracts match the local Iteration 00 baseline. Two useful remote-baseline details were preserved in this branch: the `pythonpath = ["src"]` pytest setting and the more complete Python `.gitignore` (including `.env.*` handling); this branch also adds `*.sqlite3` and `*.db` exclusions. The remote currently has `main`; `.github/workflows/ci.yml` was not present on remote `main`, so this iteration adds it.

The local implementation is on branch `iteration/01-trust-foundation`. Its latest local commits are:

```text
a30bed2 docs: finalize iteration 01 delivery and verification
27dc076 docs: clarify safe archive overlay and Git workflow
21ec0d7 docs: record remote-specific file reconciliation
51a37ad docs: record reconciled remote baseline in delivery guide
061d899 chore: reconcile Iteration 01 with live GitHub baseline
7708ce8 docs: add safe iteration 01 GitHub push guide
aba8c0c docs: record iteration 01 delivery state
8b7523f feat: add identity and consent trust foundation
f5a1071 docs: add durable project memory and codebase map
e5a4790 feat: establish engineering foundation and deterministic cashflow API
6feb028 chore: mirror remote repository baseline
```

The local branch was built in an isolated assistant workspace from a mirror of the initial Iteration 00 tree. Its commits are not assumed to be descendants of the live remote `main` commit. The delivery guide therefore uses a safe file overlay onto a fresh clone of the confirmed remote `main`, rather than recommending a blind push of this local history.

These commits are **not pushed**. Earlier connector attempts to create a remote branch or write files returned HTTP 403. The current GitHub main head was confirmed read-only using the GitHub connector; write permission remains blocked. The full source archive and push guide are provided for an authenticated local Git client. Never assume a local branch/commit was pushed.

## 2. Implemented and tested

### Iteration 00 — Deterministic cashflow API

- Python package for Python 3.12/3.13.
- FastAPI composition root, Pydantic request/response models and health/readiness endpoints.
- Framework-independent `Decimal` money and cashflow calculation domain.
- Static, curated currency precision registry; not claimed to be a full current ISO 4217 registry.
- Period validation, income/expense aggregation, essential/discretionary totals, category totals and net-cashflow-to-income percentage.
- `POST /api/v1/cashflow/analyze` calculates only over request data; no transaction ingestion or persistence.

### Iteration 01 — Identity, email verification, household and consent trust foundation

- SQLAlchemy 2 persistence models with Alembic migrations.
- SQLite local runtime and PostgreSQL dialect/migration support; PostgreSQL migration SQL was compiled offline but no live PostgreSQL server was available for runtime integration tests.
- Argon2 password hashing; generic failed-login response and dummy-hash path for unknown users.
- 256-bit opaque bearer sessions with digest-only storage, 12-hour expiry and immediate logout revocation.
- Email verification challenges: 256-bit opaque tokens, digest-only storage, one-time consumption, 24-hour expiry, previous-pending-token revocation and 60-second resend cooldown.
- Development-only log email adapter (only with `APP_ENV=development|test`) and configurable SMTP adapter. SMTP has not yet been exercised with a real provider.
- Unverified accounts cannot create/list household resources or grant/list/check/revoke consent; `/auth/me` and verification resend remain available.
- Household owner/member tables, owner-only invitation/revocation, 72-hour expiry, single-use invite acceptance and matching verified account email.
- Invitation token remains manually delivered in current iteration; API explicitly reports `manual_share_required`.
- Household member listing omits email address; membership alone never grants access to private/financial data.
- Purpose/category/recipient-specific consent grants with versioned terms, 90-day default expiry, 365-day maximum and immediate revocation.
- Commons and research purposes explicitly disallow raw transaction records, contact information and sensitive evidence categories.
- Audit events are append-only in ORM and SQLite/PostgreSQL trigger layer; audit actor/household UUIDs are pseudonymous references without foreign keys to support future deletion semantics.
- Stable application error envelope and DB+migration-aware readiness endpoint.

## 3. Live API routes

### Cashflow
- `POST /api/v1/cashflow/analyze`

### Identity
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/verify-email`
- `POST /api/v1/auth/verification/resend`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Household
- `POST /api/v1/households`
- `GET /api/v1/households`
- `POST /api/v1/households/{household_id}/invitations`
- `POST /api/v1/household-invitations/accept`
- `POST /api/v1/household-invitations/{invitation_id}/revoke`
- `GET /api/v1/households/{household_id}/members`

### Consent
- `GET /api/v1/consents/terms` (public, read-only terms)
- `POST /api/v1/consents`
- `GET /api/v1/consents`
- `POST /api/v1/consents/{consent_id}/revoke`
- `GET /api/v1/consents/check` (informational only; not a replacement for server-side enforcement)

### Health
- `GET /health/live`
- `GET /health/ready` (database plus applied migration marker)

## 4. Verification record for current source

Most recent local verification after Iteration 01 updates:
- `PYTHONPATH=src pytest -q`: **41 passed**.
- `python -m compileall -q src tests migrations scripts`: passed.
- `git diff --check`: passed.
- CI now defines a PostgreSQL 16 service job to run Alembic upgrade/downgrade/re-upgrade and execute `scripts/verify_postgres_audit.py`; this workflow has been added but has not yet run on GitHub.
- SQLite Alembic `upgrade head -> downgrade base -> upgrade head`: passed.
- PostgreSQL Alembic offline `upgrade head --sql`: generated SQL including email challenge table and partial unique indexes successfully. A PostgreSQL 16 service-backed CI job has now been added to execute the migrations and test immutable audit triggers, but its result is pending the first GitHub Actions run.
- Live local Uvicorn HTTP smoke test after the email-verification enforcement change: passed with two independently registered accounts. Both email challenges were extracted from the development-only mail adapter and verified; owner created a household and issued an invitation; matching verified invitee accepted; household membership alone returned `allowed=false`; member explicitly granted only `financial_summary` to that household; exact-scope check returned `allowed=true`; revocation changed the next check to `allowed=false`; logout invalidated the session (`/auth/me` returned 401).
- Ruff is configured but not verified in the current execution environment because the `ruff` binary was unavailable and package download was blocked by DNS/network restrictions.
- SMTP backend not tested against a real SMTP provider. Development mail adapter is exercised through test injection/local log configuration.

## 5. Known gaps and release blockers

- Test SMTP with a real provider and configure SPF/DKIM/DMARC; current invitation delivery remains manual.
- Add distributed IP/device-aware rate limiting for registration, login, verification and other sensitive endpoints; resend only has an account-level cooldown.
- Add password reset, MFA/passkeys, account recovery, session/device management, account export/deletion and retention workflows.
- Await first GitHub Actions run of the new PostgreSQL 16 migration/trigger verification job; add service-level transaction/concurrency tests after that baseline.
- Add data-access services that call `require_active_consent` in the same transaction as protected data reads. The current check route is informational only and no personal financial records are yet stored.
- Add a true durable transactional email outbox/retry state; current SMTP failure can be recovered by authenticated resend after cooldown.
- Add fine-grained household membership removal, member self-leave, owner transfer and household deletion.
- Add secrets manager, encryption-at-rest/key management, production TLS/headers, request limits, security monitoring and independent penetration testing.
- No bank import, transactions/obligations persistence, budget engine, Guardian, benefits or opportunity integrations, partner/merchant marketplace, payments/payouts, Commons exchange, RAG, graph runtime, agent missions/checkpoints or Meta model integration exists yet.
- Demo accounts/data must remain synthetic until the relevant privacy/security and provider controls are implemented.

## 6. Next iteration candidates

1. Complete PostgreSQL integration test infrastructure and harden production security (rate limiting, secrets, mail outbox, session controls).
2. Build Iteration 02 financial data foundation: accounts, transactions, recurring obligations, liabilities, budget and provenance; import CSV/manual records first and deduplicate idempotently.
3. Prepare the Day-One Personal Power Discovery slice, with one genuinely useful and evidence-grounded user outcome.
4. In a separate AI integration iteration, integrate a Meta model meaningfully. Do not send personal/confidential user data to Contributor Services. Benchmark a local Muse Glimmer workflow and Standard-tier Muse Spark/Wonder where appropriate.

## 7. Status vocabulary

- **Implemented and tested:** source exists and relevant test/runtime checks pass in the stated environment.
- **Partial:** code exists but one or more acceptance criteria or real integrations remain.
- **Designed:** documented only; no working implementation.
- **Simulated:** fixtures/stubs only; must be labelled in demo.
- **Blocked:** work cannot proceed because of a named permission, provider or dependency.

Update this file every iteration after re-reading current code, tests, local Git state and remote branch state. Never claim remote push unless it is confirmed.


## 8. Final Iteration 01 delivery verification (2026-11-03)

- Re-ran `pytest -q` without a `PYTHONPATH` override: **41 passed**. The `pythonpath = ["src"]` setting from live remote `main` is preserved.
- `python -m compileall -q src tests migrations scripts`: passed.
- `git diff --check`: passed; working tree was clean before final delivery packaging.
- Earlier in this iteration, SQLite migration upgrade → downgrade → upgrade passed; PostgreSQL migration SQL generated successfully in offline mode; live PostgreSQL was not available.
- Earlier local Uvicorn integration journey passed for two synthetic users: registration, email verification, household invitation/acceptance, membership without implicit data access, explicit financial-summary consent, revocation and logout invalidation.
- Ruff remains unverified in this runtime (binary unavailable); real SMTP delivery and live PostgreSQL runtime remain unverified. The GitHub Actions CI workflow is included in the delivery but has not been confirmed running remotely.
- Confirmed remote `main` head: `6a1b57e66536d54fe4cc96f05924d5baf868593a`. Confirmed branch creation/write attempt still returns GitHub connector HTTP 403; no Iteration 01 commit has been pushed by the assistant.
- The file-by-file change list and remote-specific additions are recorded in `docs/iterations/ITERATION-01-FILE-MANIFEST.md`. The transfer instructions are in `PUSH_TO_GITHUB.md`.

## 9. Synthetic demo dataset v1 — 2026-11-03

- Added `demo_data/synthetic_v1/` with 42 entity tables and **17,425 synthetic rows** (120 fictional customers, 55 households and 11,538 transaction fixtures).
- Included CSV, JSON, JSONL, PostgreSQL schema/seed, SQLite, HTML/PDF/PNG invoice documents, five API scenarios, business rules, regulatory mapping and reproducible generation/validation scripts.
- Built a coherent `CAM00001` Commons scenario with five users, valid event-time `COMMONS_DEMAND_AGGREGATION` consent, Jaipur/North Jaipur cohort, matching fictional education offer `OFF00004` and 5/5 quorum. Other campaigns without corresponding offers remain in demand-gathering state.
- Independent validation passed for row labels, invalid contact placeholders, PK/FK integrity, cashflow treatment, bill reconciliation, offer net-value math, event-time Commons consent, no raw financial data in Commons, campaign quorum and linked offer consistency, PDF/PNG hashes, export presence and SQLite integrity/FKs.
- This is a **demo fixture**, not a live customer base. Benefit outcomes, provider bids, partner revenue, orders, claims, applications, settlement and VIVC records are simulated. No real external action occurs.
- The Excel workbook was built before the final Commons quorum override and is intentionally excluded from this package to avoid shipping a stale view. It remains an unfinished deliverable; the canonical latest data is CSV/JSON/JSONL/SQL/SQLite plus source documents.
- PostgreSQL seed/schema has been generated but not executed against a live PostgreSQL server. SMTP, external providers and live bank/AA connections are not part of this dataset verification.
