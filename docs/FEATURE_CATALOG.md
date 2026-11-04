# Feature Catalog and Implementation Status

This is a factual status ledger, not a product promise. Update it in the same change set that changes implementation.

Status: **Implemented and tested**, **Partial**, **Designed**, **Not started**, **Simulated**.

| Area / capability | Intended behavior | Current status | Source / next acceptance |
|---|---|---|---|
| AwnNORA product identity | AwnNORA is the confirmed product/project; MyEconomy is the implementation repository/package | Confirmed | `AWNNORA_CONTEXT_MAP.md`; do not rename repository/package without a migration plan |
| Guardian invoice domain review | Evidence-linked arithmetic, confidence, duplicate and comparable-price signals | **Partial (Iterations 03–04)** | Domain review kernel is merged; local Iteration 04 adds authenticated structured invoice review, prior-bill comparison and persisted findings. OCR/model extraction/provider delivery remain absent |
| Offer net-value optimizer | Compare baseline with all costs/credits and reject unsuitable offers | **Partial (domain kernel)** | `evaluate_offer(...)` evaluates complete incremental cost; no persisted offer service, live provider catalogue or settlement |
| Commons demand aggregation | Aggregate purpose-consented fresh signals above a minimum cohort | **Partial (in-memory domain kernel)** | `aggregate_consented_demand(...)`; no persistent Commons runtime or full anti-differencing/privacy analysis |
| VIVC evidence accounting | Count only verified live outcomes with unique idempotency and one currency | **Partial (domain kernel only)** | `verified_individual_value_created(...)`; no persistent evidence/settlement ledger |
| GENIEA mission/tool policy | Bound mission states and require permission/approval/idempotency/environment match | **Partial (policy primitives only)** | `transition_mission(...)`, `authorize_tool_execution(...)`; no durable agent executor/checkpoints/outbox |
| Deterministic money/currency | Exact decimal calculation with currency precision | Implemented and tested | `domain/money.py`, `domain/cashflow.py`; currency list remains curated |
| Cashflow analysis | Income, expenses, net, essential/discretionary, categories | Implemented and tested | `application/cashflow.py`, `/api/v1/cashflow/analyze`; caller-supplied data only |
| API health/readiness | Process liveness and DB+migration readiness | Implemented and tested | `main.py`; readiness currently probes only DB/schema |
| Account registration | Unique normalized email, Argon2 password, own session | Implemented and tested | `application/identity.py`; no recovery/MFA |
| Email verification | Single-use hashed token, 24h expiry, resend cooldown, email verified gate | Implemented and tested (development adapter) | `EmailVerificationChallenge`, verification API and SMTP/log adapters; real SMTP provider not tested live |
| Session lifecycle | Random opaque bearer, hash at rest, 12h expiry, logout revoke | Implemented and tested | `application/identity.py`, `infrastructure/security.py`; no device/session dashboard |
| Login abuse protection | IP/device rate-limit, anomaly detection, credential stuffing defence | Not started | Needed before production personal data |
| Password reset/account recovery | User-controlled account recovery | Not started | Must be abuse-resistant and audited |
| MFA/passkeys | Stronger account security | Not started | Production hardening |
| Household ownership | Create/list household, role-based owner/member | Implemented and tested | `application/households.py`; delete/transfer not implemented |
| Household invitation | Owner invite, email-bound acceptance, expiry, revoke, replay protection | Partial | Core API and trust checks implemented/tested; invite token is manually delivered; SMTP invite delivery not built |
| Household isolation | Non-member cannot inspect household; membership metadata limited | Implemented and tested | Resource membership check; member email not exposed |
| Personal-data access | Read another person's financial/personal records only after exact consent | Designed / not yet connected | `require_active_consent` exists; no stored financial record service yet |
| Consent terms | Versioned purpose-specific text and allowed categories | Implemented and tested | `domain/consent.py`, `/consents/terms`; legal review required |
| Consent grant | Subject/purpose/categories/recipient/version/expiry | Implemented and tested | `application/consents.py`; not yet connected to a personal-data reader |
| Consent revocation | Immediate denial for future checks | Implemented and tested | `revoke_consent`, `has_active_consent`; downstream enforcement still future work |
| Commons privacy boundary | No raw transactions/contact/evidence passed under Commons purpose | Policy implemented and tested | `domain/consent.py`; aggregate threshold/no-inference logic not implemented |
| Research participation consent | Narrow categories, separate opt-in | Policy implemented and tested | No research pipeline exists |
| Append-only audit | Identity/household/consent changes audited and tamper-resistant via DB trigger | Implemented and tested | `application/audit.py`, migration triggers; no external WORM sink |
| Data retention/export/deletion | User export and erasure with retention policy | Designed | Needs lifecycle and legal review |
| Financial data store | User-owned accounts, persisted transactions and recurring obligations | **Partial (Iteration 02)** | `FinancialAccount`, `FinancialTransaction`, `RecurringObligation`; liabilities/budgets/goals remain future work |
| CSV/manual/bank import | Strict CSV import, provenance, idempotency, reference dedup, duplicate-review signals and monotonic provider-status reconciliation | **Partial (CSV implemented)** | `/financial/accounts/{id}/imports/csv`; batch `updated_count`; SQLite/PostgreSQL database guards: immutable imported financial facts; only monotonic provider-status changes and filling a previously missing posting timestamp are allowed; no authorized bank aggregator or bank statement connector yet. Missing treatment defaults to `IGNORE`. |
| Persisted cashflow read model | Posted-only period totals with refund/transfer/pending rules | **Implemented and tested (v1)** | `GET /api/v1/financial/cashflow`; no FX and no opening-balance reconciliation |
| Import batch inspection | Owner-scoped provenance, status and validation errors | **Implemented and tested** | `GET /api/v1/financial/imports/{batch_id}` |
| Synthetic persona loader | Load one fixture persona into an existing verified local user | **Implemented and smoke-tested** | `scripts/seed_synthetic_customer.py`; refuses production and never creates fake login accounts |
| Recurring obligation schedule | Owner-owned expected payments with due dates/frequency/autopay label | **Implemented and tested** | `RecurringObligation`; no payment mandate or scheduler |
| Budget/goals/forecast | Household allocations, cashflow forecast and scenario | Designed | Build after financial persistence |
| Personal Power Discovery | Day-one actionable report without network/bank mandatory | Designed | Next product-value slice after financial data base |
| Personal AI Representative / Guardian | Billing anomaly/refund evidence, claims drafts, follow-up | **Partial (invoice-review slice)** | Iteration 04 local API supports evidence intake, structured review, persisted findings and clarification draft; no OCR/model extraction or actual provider/claim delivery |
| Economic Defence / Shield | Scam/risk indicators and safe next actions | Designed | Never label fraud conclusively without sufficient evidence |
| Entitlement / Benefits | Official-source-grounded eligibility discovery | Designed | Eligibility possibility != approved entitlement |
| Opportunity Engine | Skill/time match to jobs, projects, training | Designed | Requires opportunity sources and capability profile |
| Knowledge-to-Economic-Asset | Turn demonstrated knowledge into paid service opportunities | Designed | Requires evidence/portfolio and demand matching |
| One-Person Enterprise | Demand research, unit economics, storefront, orders and profit | Designed | External commerce requires provider integration |
| Resource Exchange | Match capacity, resources and verified demand | Designed | Booking, trust and cancellation logic needed |
| Crisis Shield | Income shock triage, relief discovery, safe replanning | Designed | Do not default to recommending loans |
| Collective Economic Intelligence / Commons | Consent-controlled aggregate demand and resource opportunity matching | Designed | Cohort minimums, anti-inference and verified providers needed |
| Guardian evidence upload | Owner-scoped PDF/PNG/JPEG intake, size/signature validation, hash, idempotency and private blob storage | **Partial (local/demo adapter)** | `api/guardian_routes.py`, `application/guardian.py`, `infrastructure/document_storage.py`; status remains `STORED_UNSCANNED`; production needs encrypted object store, scanner, retention and restore |
| Guardian case persistence | Store invoice input/review snapshot, evidence reference, findings and owner scope | **Partial (invoice review only)** | `GuardianEvidenceDocument`, `GuardianCase`, migration `c1d4e7a9f204`; not a generalized claims/case-management service |
| Guardian action draft/approval | Draft user-facing clarification and require explicit approval | **Partial (local API)** | `/guardian/cases/{id}/draft`, `/approve-draft`; records approval to send manually; no provider contact occurs |
| Offer net-value optimizer | Evaluate all incremental spend/fees/quality/conditions and reject harmful deals | Designed | Deterministic scoring/constraints required |
| Revenue and reward ledger | Attribute eligible net revenue and 50/50 user/platform share | Designed | Contract/accounting/refund/tax/payout logic needed |
| VIVC outcome ledger | Evidence-backed realized value after additional cost | Designed | Outcome state machine and evidence provenance required |
| RAG / knowledge retrieval | Source-grounded rules, schemes, provider facts and document evidence | Designed | Retrieval is not authority for money or eligibility decisions |
| Personal capability / Commons graph | Private user graph plus carefully shared opportunity edges | Designed | Start with relational models; graph DB only if workload warrants |
| Agent runtime / durable missions | Typed tools, plan state, checkpoints, retry, resume, approvals | Designed | Mission persistence, outbox, idempotency and failure recovery needed |
| Meta AI integrations | Meaningful Muse model/SAM use for real tasks | Not started | Choose model by task; never use Contributor tier with personal/confidential data |
| Demo experience | One coherent multi-feature story with clear truth labels | Partial (API endpoints only) | Needs UI, model trace, VIVC and final-vision visualization |

## Synthetic demo fixtures (added 2026-11-03)

| Demo support | Status | Evidence / boundary |
|---|---|---|
| Synthetic multi-entity dataset | **Simulated fixture** | `demo_data/synthetic_v1/`; 42 tables, 17,425 rows, deterministic seed; not production data |
| Day-One Personal Power scenario | **Simulated fixture** | `api_scenarios/01_day_one_personal_power.json`; one-user pathway, no live banking |
| Guardian multimodal invoice cases | **Simulated fixture** | 12 synthetic PDFs/PNGs and linked bill/case/evidence records; no complaint transmitted |
| Benefits and opportunities | **Simulated fixture** | DEMO programmes and opportunity matches; no official eligibility or job placement |
| Five-person Commons quorum | **Simulated fixture** | `CAM00001`, 5/5 time-consented signals; provider/offer remains simulated |
| Offer net-value rejection | **Simulated fixture** | Deterministic fixture values; must be recomputed by live domain logic before product claims |
| Agent checkpoint/resume | **Simulated fixture** | Mission step/checkpoint and idempotency-key rows; not a production agent runtime |
| Value ledger | **Simulated fixture** | All records `SYNTHETIC_FIXTURE_ONLY`; never count in real VIVC |


## Iteration 02 evidence — Financial Data Plane v1 (2026-11-04)

- 56 automated tests passed in the local source tree.
- Provider lifecycle test covers `PENDING -> POSTED`, `POSTED -> REVERSED` and rejects `REVERSED -> POSTED` both at application and SQLite trigger layers.
- CSV without treatment is safely classified as `IGNORE`; currency-specific `amount_inr` is rejected for non-INR accounts.
- SQLite Alembic `upgrade head -> downgrade base -> upgrade head` passed.
- Real local SQLite smoke seeded `CUS00001` into an existing verified local user: first run created 2 accounts, imported 91 transactions and 5 obligations; second run reused both accounts, replayed import batches and reused obligations without duplicate rows.
- Dataset independent validator passed against the committed synthetic corpus.
- Python compileall passed. Ruff is not installed in the isolated execution runtime; local Ruff result is unverified. The merged Iteration 01 GitHub Actions run passed Ruff/pytest on Python 3.12/3.13 and PostgreSQL 16 migrations, but Iteration 02 changes still require their own CI run.
- The branch CI PostgreSQL job will now run the extended `verify_postgres_audit.py` script, which also tests the transaction immutability/status guard; until that new branch CI passes, live PostgreSQL immutability/status-guard execution remains unverified. Production SMTP, bank connectors, real financial institutions and production security controls remain unverified.


## Iteration 04 evidence — Guardian invoice-review API (local candidate, 2026-11-04)

| Capability | Status | Verification / boundary |
|---|---|---|
| PDF/PNG/JPEG evidence intake | Partial, local adapter | Verified authentication, 5 MiB streaming cap, signature check, sanitized display filename, SHA-256, owner-scoped idempotency, `STORED_UNSCANNED`; no malware scanner |
| Private evidence storage | Partial, local/demo only | Generated object keys and restrictive directory/file permissions; no encryption-at-rest/KMS or production object-store adapter |
| Invoice review API | Partial, structured input | Deterministic calculation and prior-invoice comparison; values are manually/user supplied, not OCR/Meta extracted |
| Case/audit state | Partial, persisted | Owner-scoped evidence/case FK, idempotency hashes, snapshots, findings and append-only audit events |
| Draft/approval | Partial, no external delivery | Deterministic clarification draft; approval means user may send it manually; no email/provider API side effect |
| Synthetic Guardian workflow | Simulated, local test | Three fictional PDFs, structured payloads, page/line locators and SHA-256 manifest; no real customers/providers |
| Local verification | Passed except stated gaps | 83 pytest tests, compileall, SQLite migration lifecycle and original 42-table/17,425-row dataset validator passed. Ruff, Python 3.12 and live PostgreSQL 16 migration test are unverified. |


<!-- AWNNORA-TRANSFER-ITERATION-05 -->
## Transfer overlay capability addition

| Area / capability | Intended behavior | Local overlay status | Acceptance remaining |
|---|---|---|---|
| Personal Mode Power Report | Owner-private report from persisted posted cashflow, potential duplicates and recurring obligations | Implemented as additive candidate in `src/myeconomy/{domain,application,api}/personal_power*.py`; package-level domain tests passed | Apply to target checkout; run full API/integration suite, migration/readiness and first-user runbook |
| First-user local journey | Verify user, seed one synthetic persona through existing services, call Personal Power endpoint | Implemented as `scripts/awnnora_first_user_journey.py` | Run against an isolated local DB and dedicated `@example.invalid` account |
| Scenario Lab | Reproducible product-level scenario workload and invariant validator | Implemented; 46 templates / 1,150 generated default runs validated | Wire fixtures to live subsystem acceptance tests as each engine is built |
