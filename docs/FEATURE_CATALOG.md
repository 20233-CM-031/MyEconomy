# Feature Catalog and Implementation Status

This is a factual status ledger, not a product promise. Update it in the same change set that changes implementation.

Status: **Implemented and tested**, **Partial**, **Designed**, **Not started**, **Simulated**.

| Area / capability | Intended behavior | Current status | Source / next acceptance |
|---|---|---|---|
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
| Financial data store | Accounts, transactions, obligations, liabilities, budgets | Not started | Iteration 02 schema + provenance |
| CSV/manual/bank import | Idempotent import, dedup, reconciliation, supported bank provider | Not started | Start with CSV/manual data; bank aggregator only with credentials and permission |
| Budget/goals/forecast | Household allocations, cashflow forecast and scenario | Designed | Build after financial persistence |
| Personal Power Discovery | Day-one actionable report without network/bank mandatory | Designed | Next product-value slice after financial data base |
| Personal AI Representative / Guardian | Billing anomaly/refund evidence, claims drafts, follow-up | Designed | No actual provider/claim integration yet |
| Economic Defence / Shield | Scam/risk indicators and safe next actions | Designed | Never label fraud conclusively without sufficient evidence |
| Entitlement / Benefits | Official-source-grounded eligibility discovery | Designed | Eligibility possibility != approved entitlement |
| Opportunity Engine | Skill/time match to jobs, projects, training | Designed | Requires opportunity sources and capability profile |
| Knowledge-to-Economic-Asset | Turn demonstrated knowledge into paid service opportunities | Designed | Requires evidence/portfolio and demand matching |
| One-Person Enterprise | Demand research, unit economics, storefront, orders and profit | Designed | External commerce requires provider integration |
| Resource Exchange | Match capacity, resources and verified demand | Designed | Booking, trust and cancellation logic needed |
| Crisis Shield | Income shock triage, relief discovery, safe replanning | Designed | Do not default to recommending loans |
| Collective Economic Intelligence / Commons | Consent-controlled aggregate demand and resource opportunity matching | Designed | Cohort minimums, anti-inference and verified providers needed |
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
