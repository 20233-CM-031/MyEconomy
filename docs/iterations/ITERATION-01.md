# Iteration 01 — Identity, Email Verification, Household and Consent Trust Foundation

- **Branch:** `iteration/01-trust-foundation`
- **Status:** Core slice implemented and locally tested; PostgreSQL service-backed CI added, production hardening remains open.
- **Scope owner:** Project team.
- **Date:** 2026-11-03.

## 1. Problem

The product will eventually process personal financial, household, skills, opportunity and support data. Before data imports, AI agents or Commons sharing exist, the system needs an enforceable identity and authorization foundation. Household membership must never silently authorize access to another person's records.

## 2. User stories

- As a person, I can register, verify control of my email, log in and revoke a session.
- As a verified person, I can create a household and invite a person by email.
- As an invitee, I can accept a single-use invitation only when my verified account email matches the invitation.
- As a household member, I can see limited membership information but cannot access another person's financial data merely because we share a household.
- As a person, I can inspect terms and grant purpose/category/recipient-scoped consent with a version and expiry.
- As a person, I can revoke my consent and future checks deny the revoked scope immediately.
- As a future data service, I can require an active exact-scope consent inside my transaction.

## 3. Out of scope

- Full consumer identity proofing, password reset, MFA/passkeys or account recovery.
- Email invitation delivery, passwordless login or production-grade SMTP outbox.
- Household member removal, self-leave, ownership transfer/deletion.
- Reading/storing user financial transactions or documents.
- Bank aggregator, merchant, partner, research, payment, benefits or complaint integrations.
- LLM/Meta model integration and agent execution.
- Production certification, penetration test, legal review or compliance attestation.

## 4. Design and invariants

1. Passwords use Argon2id; no plaintext storage/logging.
2. Session, email-verification and household-invitation tokens are high-entropy opaque secrets; persist only SHA-256 digest.
3. Session TTL is 12h; email verification TTL is 24h; invitation TTL is 72h.
4. Email verification is single-use. Reissuing revokes the previous active token; resend cooldown is 60 seconds per account.
5. Household and consent APIs require `email_verified=True`.
6. Only a household owner can invite/revoke invitations in this iteration.
7. Invitation acceptance requires a nonexpired, nonrevoked, unused token and matching verified account email.
8. Membership does not imply data access.
9. Consent must match subject, purpose, category, recipient type/id, version and expiry.
10. Commons/research categories intentionally exclude raw transaction records, direct contact details and support evidence.
11. Revocation blocks future consent checks.
12. Future readers must call `require_active_consent` in the same transaction as protected data access.
13. Audit records are append-only at ORM and database trigger levels.
14. Models do not make authorization or financial decisions.

## 5. Data model

Added `EmailVerificationChallenge`; persisted `User`, `AuthSession`, `Household`, `HouseholdMembership`, `HouseholdInvitation`, `ConsentGrant` and `AuditEvent`. Migration chain:

- `8ec10b31a771`: identity/session/household/invitation/consent/audit schema and immutable audit triggers.
- `3b2e7f4a9c10`: one-time email verification challenge table with unique pending challenge per account.

SQLite and PostgreSQL migration dialects are supported. PostgreSQL was checked with offline SQL generation; no live PostgreSQL service was available.

## 6. API surface added

- Register, verify email, resend verification, login, logout, current account.
- Household create/list, issue invitation, accept invitation, revoke invitation, list members.
- Public consent terms; authenticated consent create/list/revoke/check.
- DB+migration-aware readiness.

See `docs/CODEBASE_MAP.md` for exact route-to-service call paths.

## 7. Acceptance evidence

- [x] Registration normalizes email and hashes password.
- [x] Password is not stored in plaintext.
- [x] Session token is not stored in plaintext.
- [x] Session expires and logout revokes it.
- [x] Email challenge is digest-only, 24h, one-time and resend cooldown enforced.
- [x] Household/consent actions reject unverified users.
- [x] Owner-only invitation and email-bound acceptance.
- [x] Expired/revoked/replayed invitation denied.
- [x] Member-list response omits member email.
- [x] Membership does not imply data consent.
- [x] Purpose/category/recipient/version/expiry validation.
- [x] Commons and research cannot authorize raw transaction records.
- [x] Revocation immediately changes consent checks.
- [x] Direct audit UPDATE fails in local SQLite test.
- [x] `pytest -q`: 41 passed after latest change.
- [x] Python compileall and `git diff --check` passed.
- [x] SQLite migration upgrade/downgrade/upgrade passed.
- [x] PostgreSQL migration offline SQL generated.
- [x] Live Uvicorn HTTP smoke: two accounts registered and verified; household invite issued/accepted; membership without consent denied; scoped financial-summary consent granted; revocation denied the next check; logout invalidated session.
- [x] PostgreSQL 16 GitHub Actions migration/trigger verification job defined; run result remains pending until branch is pushed and CI executes.
- [ ] Ruff lint/format; tool unavailable in this execution environment.
- [ ] Live SMTP provider test.
- [ ] First GitHub Actions PostgreSQL 16 migration/trigger job result.
- [ ] Live PostgreSQL concurrency/integration tests.

## 8. Known limitations

- Development email backend deliberately logs one-time verification tokens only when `APP_ENV=development` or `test`. It is forbidden elsewhere.
- SMTP adapter is implemented, but credentials/provider have not been tested. No durable mail outbox/retry worker.
- Invitation email delivery is not implemented; invite API returns the token once with `manual_share_required`.
- Verification proves inbox control, not legal identity.
- IP/device-aware login rate limiting, password recovery, MFA, session management and production security hardening are not implemented.
- No personal data reader currently enforces consent; only grant/check policy and enforcement helper exist.
- No live personal financial data should be used in the hackathon demo; use synthetic records.

## 9. Changes to carry forward

- Add PostgreSQL service-backed integration tests and concurrency coverage.
- Add production mail outbox and real SMTP delivery test.
- Add abuse controls and password recovery/MFA.
- Build the financial data foundation with import provenance/idempotency.
- Integrate consent enforcement into every actual data reader/writer.
- Start meaningful Meta model integration only after a task and data-tier policy are defined.

## 10. Scorecard contribution

- **Impact (30%):** enables secure individual and household onboarding, a prerequisite for the Personal Mode and Commons vision; no measured economic outcome yet.
- **Meta AI tooling (25%):** no Meta model is integrated in this iteration. Do not claim this category is satisfied.
- **Technical depth (20%):** adds persisted identity, hashed token lifecycle, versioned consent, data ownership, immutable audit and migration tests.
- **Demo (25%):** enables a real trust journey with synthetic users; the final visual product demo remains future work.

## 11. File-level manifest and future continuation

The exhaustive repository-path manifest (including source responsibilities, dependencies, tests, migration ownership and rollback notes) is maintained in [`ITERATION-01-FILE-MANIFEST.md`](ITERATION-01-FILE-MANIFEST.md). Future contributors must read `AGENTS.md`, `docs/PROJECT_MEMORY.md`, `docs/CODEBASE_MAP.md`, `docs/PROJECT_STATUS.md`, and this manifest before modifying the system.
