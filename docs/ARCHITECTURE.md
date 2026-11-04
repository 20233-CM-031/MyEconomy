# AwnNORA System Architecture — Current Implementation and Target Design

Canonical product/system map: [`AWNNORA_CONTEXT_MAP.md`](AWNNORA_CONTEXT_MAP.md).

This document separates the code that exists from the full product architecture. Live `main` includes Iteration 03 (PR #3); Iteration 04 Guardian API details below describe a locally tested candidate that has not been pushed.

## 1. Product/system boundaries

The product aims to deliver individual economic agency first, then collective opportunity intelligence through consent-controlled signals. The eventual system includes:

- **Personal Mode:** private personal context, cashflow, protection, benefits, opportunity, knowledge-to-income, crisis and enterprise workflows. Must deliver a useful action with one user.
- **Commons Mode:** purpose-limited aggregation of consented demand/capabilities/resources, with cohort thresholds and anti-inference protections.
- **MAKOS:** intended operational workspace and durable workflow surface.
- **GENIEA:** intended agent orchestration layer for planning, agent delegation, tool execution, recovery and mission coordination.
- **KRN:** intended knowledge/context and Collective Opportunity Graph layer, with private graph partitions and explicitly authorized shared edges.

AwnNORA is the product/system. MAKOS, GENIEA and KRN are first-class architectural systems with the responsibilities described above. They are not yet separate application packages in the repository. Iteration 03 now contains a small framework-independent GENIEA policy/domain kernel; durable agent runtime, MAKOS UI and KRN persistence remain unimplemented. See `AWNNORA_CONTEXT_MAP.md` for the full canonical map.

## 2. Implementation architecture today

A Python/FastAPI modular monolith, organized around `api -> application -> domain`, with application services calling infrastructure adapters/persistence.

- **API:** FastAPI routers, Pydantic 2 schemas, auth dependencies and safe error mapping.
- **Application:** transaction-owning use cases for identity, email verification, sessions, households, invitations, consent, audit and cashflow translation.
- **Domain:** pure cashflow/money logic, typed consent vocabulary/policy, stable application errors, and the Iteration 03 economic-intelligence kernel (`economic_intelligence.py`).
- **Infrastructure:** SQLAlchemy models/session, Alembic, Argon2/session primitives, email delivery adapter.
- **Persistence:** SQLite for local/test; PostgreSQL supported through SQLAlchemy/psycopg and Alembic. Live PostgreSQL integration is still unverified.

Do not split into microservices until independent scale, security isolation, deployment ownership or reliability needs demonstrate the value.

## 3. Actual request flows

### Authenticated request

HTTP bearer token -> `require_authentication` -> SHA-256 token digest lookup -> session status/expiry/revocation -> active user -> `AuthContext`.

Household and consent routes additionally call `require_verified_authentication`; account email must be verified first.

### Email verification

Register -> normalize email -> Argon2 hash -> persist user -> create 12h session -> create 256-bit email challenge, store SHA-256 digest and 24h expiry -> send via development log adapter or SMTP adapter -> client posts token -> verify digest/single-use/expiry -> set email verified -> revoke other pending challenges -> append audit event.

Log delivery is allowed only when `APP_ENV=development` or `test`. SMTP is environment-configured; it has not been tested against a live provider yet.

### Household invitation

Verified owner -> create household and owner membership -> owner issues invite -> store digest + invited email + 72h expiry -> invitee authenticates and verifies their email -> accepts token -> email comparison + replay/expiry/revocation checks -> create membership. Membership is deliberately separate from consent. Invitation token is currently returned once with `manual_share_required`; delivery by email is not implemented.

### Consent

Verified user -> fetch current terms -> submit purpose/categories/recipient/version/explicit confirmation/expiry -> deterministic domain matrix -> persist grant + audit -> future data reader must call `require_active_consent` in the same transaction as protected access -> revocation blocks future use.

The `/consents/check` route is informational only. No private financial data reader exists in the current implementation.

### Cashflow

Pydantic request -> `run_cashflow_analysis` -> pure domain validation and Decimal calculations -> API response. The input is not persisted.

## 4. Data model currently implemented

| Entity | Responsibility | Invariants |
|---|---|---|
| `User` | Account and email verification | Normalized unique email, Argon2 hash, `email_verified` and active flag |
| `AuthSession` | Opaque session lifecycle | 256-bit random token, hash-only storage, expiry/revocation |
| `EmailVerificationChallenge` | Account email control challenge | Hash-only token, single-use, 24h expiry, one pending per user |
| `Household` | Named household boundary | Owner references account; membership relation controls access |
| `HouseholdMembership` | User role in household | One membership per user/household, constrained role |
| `HouseholdInvitation` | One-time invite | Owner issuer, invited email, expiry/revoked/accepted state, token hash |
| `ConsentGrant` | User authorization record | Subject, purpose, category list, recipient, terms version, expiry, status |
| `AuditEvent` | Append-only audit record | Pseudonymous references, no FK dependency, ORM/database mutation rejection |

## 5. Trust and authorization design

- Authentication proves possession of an account session.
- Email verification proves access to that email inbox, not legal identity.
- Resource authorization proves membership/role for the exact household/resource.
- Consent proves a user authorized the specified purpose, data categories and recipient, within the time window.
- The data-access service must check all of these at the point of actual data access; a UI checkbox or preflight consent check is insufficient.
- Models never decide authorization or retrieve arbitrary rows. A future model agent receives typed tools that call application services, which enforce access.

### Guardian evidence intake and invoice review — Iteration 04 local candidate

The current API vertical flow is:

`verified user -> bounded upload -> MIME/signature/size check -> SHA-256 -> owner-scoped idempotency -> local private blob + metadata -> STORED_UNSCANNED -> user-submitted structured invoice and evidence locators -> deterministic invoice arithmetic/evidence/confidence/prior-invoice review -> persisted owner-scoped case + audit -> clarification draft -> explicit approval state for manual sending`.

The database stores `GuardianEvidenceDocument` and `GuardianCase`. A composite foreign key ensures a case cannot reference another owner's evidence document. Per-owner idempotency constraints and request/source hashes make identical retries replayable and changed payload reuse conflict. The case write and audit event share a transaction; unique-key races are handled as idempotency conflicts/replays.

The document adapter currently uses a local filesystem path rooted at `AWNNORA_DOCUMENT_ROOT`, generated UUID filenames, restrictive POSIX permissions and atomic rename. That adapter is for trusted local/demo use only. Files remain `STORED_UNSCANNED`; there is no antivirus/malware scan, OCR, PDF parsing, Meta model call, page-region locator verification, retention/deletion lifecycle, encryption-at-rest or KMS integration. The review fields are submitted by the user/client and are not extracted from the uploaded binary.

Draft approval records an internal state only. It does not dispatch email, contact a provider, submit a complaint, make a payment, cancel a service or otherwise perform an external side effect.

## 6. Target data and intelligence planes

These planes are architecture targets and are not yet built:

1. **Data Plane:** financial accounts, transactions, obligations, liabilities, budgets, resource listings, provenance, migrations, outbox and audit.
2. **Knowledge/RAG Plane:** trusted source ingestion for official benefits, provider terms, public information and authorized documents. Each source requires provenance/version/date and extraction evidence.
3. **Logic & Intelligence Plane:** deterministic finance calculations, rule evaluation, opportunity matching, constraints, offer net-value optimizer, eligibility explanation and VIVC accounting.
4. **Agent & Automation Plane:** mission state machines, typed tool registry, checkpoint/resume, retries, idempotency, timeout budgets and approvals.
5. **Graph Plane / KRN:** begin with relational relationships and carefully scoped edges; only adopt graph storage when measured traversals justify it.
6. **Workspace / MAKOS:** user-visible task state, evidence, status, approvals and audit traces.
7. **Orchestration / GENIEA:** cross-plane plans and specialized agent delegation, without bypassing deterministic application services.

## 7. Model integration strategy

A provider/model abstraction should be introduced only with a specific task requiring it.

- Local open-weight Muse Glimmer is a candidate for private, on-device document/context reasoning and agent workflows. Benchmark the actual runtime/hardware before claiming feasibility.
- Muse Spark / Muse Wonder through Standard services are candidates for complex multimodal reasoning, external research and task planning when hosted inference materially helps.
- Never send personal/confidential user information to Contributor Services. Use Standard Services where permitted for personal information and/or process sensitive context locally. Use synthetic data in hackathon demos.
- Muse Image is not an option for this India-based project under the current Meta geographic policy.
- SAM 3.1 is optional when image/video region segmentation adds measurable value; do not include it decoratively.
- All outputs must be schema-validated and domain checked; LLM output never becomes authoritative money or access-control logic.

## 8. Long-running agent reliability

Future missions must persist:
- mission ID, owner, tenant/household scope and permission snapshot;
- task plan/version, completed/pending/failed steps;
- input/output references and evidence/provenance;
- model/provider/version and tool contracts;
- idempotency keys and external request IDs;
- checkpoint, retry count, timeout/deadline and compensation state;
- pending human approval and approval expiry;
- terminal outcome and verified-value evidence.

When a 50-step workflow fails at step 49, re-read the durable mission and external state, then resume from the last valid checkpoint. Never blindly replay a side effect. Request user input only for the unresolved decision.

## 9. Financial and value logic

- `Decimal` only for money; currency accompanies every amount.
- No mixed currency totals without an explicit, sourced and dated FX conversion.
- Offer net value = real benefit/funding minus incremental spend, fees, delivery, lock-ins, quality penalties and other costs.
- Deterministic constraints decide whether an offer is admissible; model summaries cannot override them.
- VIVC counts only evidence-backed realized outcomes, net of additional costs. Estimates, opportunities and attempts stay separate.
- Proposed 50/50 sharing applies only to a contractually defined eligible net revenue pool and needs a proper transaction/reconciliation/payout ledger.

## 10. Database / migrations / runtime

- SQLAlchemy 2 ORM and Alembic migrations.
- `DATABASE_URL` selects the DB; `.env.example` is local development only.
- SQLite enables FK enforcement per connection.
- Migrations are controlled release steps, not executed independently by every app replica.
- `/health/ready` verifies DB connectivity and the Alembic version marker.
- Current migrations install database triggers that reject audit UPDATE/DELETE for SQLite and PostgreSQL.

## 11. Observability and operational requirements still needed

- Structured JSON logs with correlation/request/mission IDs and PII redaction.
- Metrics for latency/error/DB pool, model usage/cost, tool outcomes, queue age, retries and VIVC states.
- OpenTelemetry traces across API, application and external providers.
- Managed secrets/KMS, TLS, backup/restore tests, rate limiting, quotas, incident response and retention/deletion jobs.
- Live PostgreSQL and SMTP CI integration tests.

## 12. Architecture change rule

Every new storage technology, service boundary, LLM/provider, graph engine or queue requires an ADR explaining: concrete use case, alternatives, workload evidence, operational cost, privacy/security implications, failure behavior, migration/rollback and how it improves the actual acceptance criteria.
