# Feature Catalog and Implementation Status

This catalog is a status ledger, not a promise that every planned feature is present. Update it in the same change set that adds/removes feature behavior.

Status values: **Implemented** = code and tests exist in this repository; **Partial** = some production behavior exists but acceptance criteria are incomplete; **Designed** = intended behavior/architecture documented only; **Not started** = no meaningful implementation; **Simulated** = demo fixture only and never represent as live.

| Area / capability | What it must do | Current status | Evidence / next work |
|---|---|---|---|
| Cashflow calculation | Calculate income/expense/net/essential/discretionary/category totals on user-supplied entries | **Implemented (Iteration 00 slice)** | `src/myeconomy/domain/cashflow.py`, `domain/money.py`, API and tests. In-memory request only. |
| API health/readiness | Liveness and readiness endpoints | **Implemented (basic)** | `main.py`; readiness is static until dependencies exist. |
| User identity/authentication | Accounts, sessions, secure identity, account recovery | **Not started** | Iteration 01. |
| Household/tenant isolation | Ownership boundaries and member roles | **Not started** | Iteration 01; must be tested against cross-user access. |
| Consent ledger | Purpose-specific grant, scope, expiry, revocation and audit | **Not started** | Iteration 01; required before personal data sharing. |
| Financial data store | Accounts, transactions, recurring obligations, liabilities, budgets | **Designed** | Iteration 02; no DB or migrations today. |
| Data import/reconciliation | CSV/manual import first, bank aggregation only with authorized provider; deduplication/provenance | **Designed** | Iteration 02. |
| Budgeting and goals | Household budgets, allocation, forecasts and scenarios | **Designed** | Future financial domain after persistence. |
| Personal Power Discovery | Day-one onboarding and prioritized report with one useful action | **Designed** | Iteration 03; must work without network/bank requirement. |
| Guardian / Personal AI Representative | Detect potential billing/contract issues, evidence, draft, follow-up | **Designed** | Iteration 04; actual submission requires supported provider and approval. |
| Economic Defence / Shield | Suspicious-message/payment/fee/contract risk explanation with evidence and uncertainty | **Designed** | Iteration 04; no unverified fraud certainty. |
| Benefits / Entitlement Engine | Source-grounded benefits catalogue and eligibility explanations | **Designed** | Iteration 05; official confirmation remains external. |
| Opportunity Engine | Skills/time/experience-to-jobs/projects/training matching and tracking | **Designed** | Iteration 05. |
| Capability / Knowledge Graph | User-owned evidence-backed skills and knowledge graph; monetize skills | **Designed** | Iteration 05 and graph foundations. |
| One-Person Enterprise Engine | Demand discovery, unit economics, catalogue, operations, orders and profit | **Designed** | Iteration 06. |
| Resource Exchange | Match verified supply, demand, availability and capacity | **Designed** | Iteration 07. |
| Commons / Collective Economic Intelligence | Consent-protected aggregate demand, provider/resource matching, group commitments | **Designed** | Iteration 08; privacy thresholds and inference protection required. |
| Offer/value optimizer | Compare full net value and reject offers with harmful conditions/extra spend | **Designed** | Requires deterministic offer and terms model. |
| VIVC outcome ledger | Verify recovery, savings, earnings, benefits and prevented fees after extra costs | **Designed** | Needs evidence lifecycle and auditable event ledger. |
| Sponsor/partner monetization | Commissions, sponsored benefits and transparent net revenue share | **Designed** | No partner APIs or revenue transactions. |
| Proposed 50/50 net revenue sharing | Attribute eligible net revenue and allocate user/platform shares transparently | **Designed** | Contract definitions, accounting, refunds, tax and payout controls required. |
| Crisis Shield | Crisis detection, safe prioritization, relief/opportunity discovery and consented aid | **Designed** | Iteration 10. |
| Agent runtime / GENIEA direction | Typed tools, plans, policy, checkpoints, durable state, retries, resume and approvals | **Designed** | Iteration 09; no LLM or agent code today. |
| MAKOS operational workspace | Tasks, approvals, evidence and workflow interface | **Designed** | Future user/operator experience; not in current code. |
| KRN / Collective Opportunity Graph | Private and shared knowledge graph relationships | **Designed** | Graph schema first; do not add graph database before query needs justify it. |
| RAG / evidence retrieval | Trusted retrieval over authoritative sources and user-authorized docs with provenance | **Not started** | Needs source registry, versioning and prompt-injection defense. |
| Meta AI integration | Relevant model/tool integration for extraction, multimodal evidence and agent planning | **Not started** | Verify current hackathon rules and model eligibility before selection. |
| Durable workflow resume | Resume interrupted long task from last verified checkpoint without repeating side effects | **Not started** | Requires persisted mission state, idempotency, step ledger and external state reconciliation. |
| Demo end-to-end network | A single narrative across personal value and Commons with honest live/simulated labels | **Designed** | Iteration 10; synthetic/demo fixtures must be visibly marked. |

## Minimum acceptance doctrine

Every row moving to Implemented must link to code, migration if relevant, tests, runtime proof and known limitations. A mock, UI placeholder, prompt template or diagram alone does not qualify. A feature may be partially implemented when some sub-workflows are real, but the catalog must say exactly which ones.
