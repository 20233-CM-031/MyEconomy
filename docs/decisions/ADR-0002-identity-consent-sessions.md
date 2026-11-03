# ADR-0002 — Persisted Identity, Email Verification and Purpose-Bound Consent

- **Status:** Accepted for Iteration 01; production hardening remains required.
- **Date:** 2026-11-03

## Context

The product handles economic context. Before financial data, household collaboration or Commons signals are introduced, a person must control their account, access only their own resources, and explicitly authorize each sharing purpose and data category.

## Decisions

1. Use opaque 256-bit bearer session tokens; store only SHA-256 digests because tokens have high entropy.
2. Hash passwords using Argon2id via `argon2-cffi`.
3. Require email verification before household and consent operations. Verification tokens are random, hashed at rest, single-use, expire after 24 hours, and prior active tokens are revoked when a new one is issued.
4. Support a development-only log mail adapter and an SMTP adapter configured through environment variables. Log mode must be rejected whenever `APP_ENV` is not `development` or `test`.
5. Persist household, membership and invitation separately. A household owner invites; the invitee must authenticate with the matching verified email. Membership never grants personal-data access.
6. Persist consent separately from membership and bind it to a purpose, approved categories, recipient type/id, exact terms version and bounded expiry.
7. Revocation is immediate. Every future data-reader must enforce consent inside the same transaction as its data access; the exposed check endpoint is informational only.
8. Maintain append-only audit records at ORM and database trigger level. Do not store raw passwords or tokens in audit details.
9. Start with SQLAlchemy 2, Alembic, SQLite local tests and PostgreSQL support. Do not add a graph DB, queue or microservice before the workload justifies it.

## Consequences

- Users can create an account but cannot create a household or grant consent until email is verified.
- Local setup can test the verification flow without an SMTP account, but the log adapter is not suitable for production.
- The SMTP adapter still needs a live provider test, retry/outbox durability and delivery observability before production.
- The audit data model deliberately uses pseudonymous UUID references rather than foreign keys for actor/household so future account deletion need not mutate immutable audit events.
- Commons and research consent deliberately exclude raw transaction records, direct contact information and case evidence.

## Rejected alternatives

- Treating household membership as financial-data authorization: rejected because it violates individual agency and creates a serious privacy boundary failure.
- Storing bearer tokens in plaintext: rejected because a database read should not directly yield reusable tokens.
- Letting the language model decide access rights: rejected; authorization is deterministic application/domain logic.
- Starting with distributed microservices and multiple data stores: rejected until measured scale or deployment isolation justifies the operational cost.
