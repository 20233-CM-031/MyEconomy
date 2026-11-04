# AwnNORA — From Demonstration to Real-Time Product

This document distinguishes a working demonstration from a system safe to serve real households. The current repository is a modular-monolith foundation; the components below are target engineering architecture, not claims of deployed infrastructure.

## 1. Keep the core simple; make execution durable

Retain the modular monolith while the domain boundaries are still evolving. Add independently deployable workers only where workloads require them (document scanning/OCR, mission execution, scheduled source refresh, notifications and partner reconciliation). Do not split every capability into a microservice prematurely.

```text
MAKOS web/mobile experience
  | HTTPS / authenticated API / server-sent events
FastAPI application boundary
  | identity + purpose consent + authorization + rate limits
Application use cases
  | typed commands / queries / transaction boundary
Deterministic domain kernel
  | money / eligibility / matching / constraints / VIVC
PostgreSQL  <----> transactional outbox + audit
  |                         |
Encrypted private object    +--> durable worker queue / GENIEA
storage + KMS                     | leases / retry / checkpoint / reconcile
  |                               +--> approved tool adapters
quarantine -> scanner -> OCR/model gateway -> evidence validation
  |                               |
KRN private facts / provenance  approved external systems (sandbox first)
  |                               |
MAKOS case, mission and outcome timeline <--- provider acknowledgements/settlement
```

## 2. Synchronous versus asynchronous work

**Synchronous (short, deterministic):** authentication, consent checks, account reads, CSV validation/import, simple cashflow analysis, offer arithmetic and report assembly. Return a normal API response only after the database transaction commits.

**Asynchronous (slow or externally uncertain):** malware scans, OCR/multimodal extraction, long agent missions, public-source crawling, partner API actions, benefit/application status checks, booking/settlement and notification delivery. Use a durable job/mission record and transactional outbox. Return an accepted job/mission identifier; expose `QUEUED`, `RUNNING`, `WAITING_APPROVAL`, `RETRY_WAIT`, `RECONCILING`, `SUCCEEDED`, `PARTIAL`, `FAILED` or `CANCELLED` states with timestamps and retry history.

Use server-sent events or WebSockets only as a notification layer over persisted state. A dropped browser connection must not lose a mission or cause a duplicate side effect. On reconnect, the client reads the authoritative timeline from the API.

## 3. Durable mission and tool protocol

Each GENIEA mission needs:
- immutable mission intent, owner, tenant, environment, scope, consent references and policy version;
- a planned step list with typed tool contract/version and explicit read/write scope;
- step status, attempt count, lease owner/expiry, timeout, idempotency key and input/output hashes;
- checkpoints with schema version, source facts and evidence references;
- approval records bound to exact action payload hash, scope, user, expiry and revocation status;
- outbox record for every external side effect, provider idempotency key where supported, correlation ID and reconciliation status;
- append-only event history and cancellation/compensation route.

Workers claim work with compare-and-set/lease semantics. A stale lease may be reclaimed, but the worker must first determine whether the previous attempt produced an external effect. If provider state is unknown after timeout, enter `RECONCILING`; do not blindly replay. “Exactly once” is not promised unless the provider contract proves it.

## 4. Document trust and AI extraction path

The existing Guardian upload state `STORED_UNSCANNED` is not safe input for OCR or a model. A production path must fail closed:

`RECEIVED -> QUARANTINED -> SCANNING -> CLEAN | REJECTED | SCAN_FAILED`

Only `CLEAN` can proceed to a sandboxed parser/OCR worker. Scanner identity/version, scan time, file digest, result and policy must be persisted. Missing scanner, timeout, corrupt PDF, polyglot, archive bomb, parser error or ambiguous type never becomes `CLEAN`.

Extraction output is a proposal, not truth. Persist field value, currency, page/region/text span, document SHA-256, extractor/model version, prompt/schema version, confidence and extraction warnings. Validate locator existence, schema, arithmetic and source-hash equality deterministically. Low confidence or unsupported content abstains. The model has no unrestricted network, database or provider tools. Human review precedes any consequential use.

## 5. Privacy, money and environment boundaries

- Private records are owner-scoped by default; every data query must be authorized at the data-access boundary.
- Household membership is not financial-data consent.
- Consent is purpose/category/recipient/time bound and rechecked at execution time; revocation blocks future access and side effects.
- Commons receives approved, minimized signals only. Minimum cohort size is not differential privacy; prevent differencing, intersection attacks, rare-attribute leakage and repeated-query inference.
- Monetary values use integer minor units or validated Decimal with explicit currency. Never mix currencies without a sourced, dated FX record.
- Environment is a typed value: `SYNTHETIC`, `SANDBOX`, `LIVE`. Adapters reject mismatches. Synthetic records can never call a live adapter or count as real VIVC.
- LLM output cannot calculate or settle money, grant consent, prove official eligibility, declare fraud, or mark VIVC verified.

## 6. Operational baseline before real users

| Area | Required engineering work before production personal data |
|---|---|
| Persistence | PostgreSQL integration/concurrency tests, migration rollback, connection pooling, backups and restore drill |
| Secrets and transport | TLS, secrets manager, key rotation, KMS/envelope encryption, private object access policy |
| Identity | password recovery, MFA/passkeys, login abuse controls, session/device revocation |
| Privacy lifecycle | data export, retention/deletion, purpose limitation, consent revocation and audit retention |
| Document processing | fail-closed malware scanner, quarantine, parser sandbox, quotas, orphan reconciliation |
| Agent reliability | durable queue/outbox, worker leases, retry budgets, replay/reconciliation and cancellation |
| Observability | structured redacted logs, traces, metrics, audit correlation, security alerting and incident runbooks |
| Integration | partner contract, lawful authority, sandbox tests, webhook signature verification and settlement reconciliation |
| User safety | accessible approval flows, clear uncertainty/limitations, complaints/escalation and support process |
| Governance | jurisdiction/role legal review, privacy assessment, threat review and independent penetration testing |

## 7. Suggested runtime service objectives (proposed, not measured)

Establish baselines with load tests before treating these as commitments:

- Health and basic authenticated reads: p95 under 300 ms on the target deployment.
- Personal Power Report with 12 months of indexed transaction history: p95 under 1 s for one currency and owner.
- CSV import: bounded streaming, idempotent commit; return batch status only after durable persistence.
- Document scan/OCR: asynchronous with a visible job state and bounded timeout; no unbounded HTTP request wait.
- Mission status: durable within the same transaction as each state transition; event delivery may be at-least-once and clients deduplicate by event ID.
- No silent loss of acknowledged writes; recover from worker restart, queue redelivery and lost client connection.

These are candidate targets; measure the actual environment and tune indexes, concurrency and resource allocation accordingly.

## 8. Real-user release gates

1. **Synthetic demo:** generated corpus only; every screen labels it; external calls disabled.
2. **Sandbox integration:** dedicated test credentials and provider sandboxes; no production identifiers or real payments.
3. **Internal pilot:** real users only after access controls, encryption, retention, backups, rate limits, incident response and legal/privacy review are approved; keep external actions disabled by default.
4. **Partner pilot:** signed contracts/authority, user opt-in, strict action scopes, signed webhooks, retries and reconciliation.
5. **General availability:** independent security test, recovery exercise, monitored SLOs, user support and auditable value settlement.

A demo that works locally is not proof of a real-time production deployment. The release gates make that distinction explicit.
