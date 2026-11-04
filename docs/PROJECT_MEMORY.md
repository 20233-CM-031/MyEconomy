# Project Memory — AwnNORA (implementation repository: MyEconomy)

> **Purpose:** Durable project context for future engineering sessions, contributors and AI coding assistants. This is the canonical high-level memory of the product's intent, architecture, constraints and decisions. It must be updated when decisions or capabilities change.
>
> **Last reconciled with source tree:** 2026-11-04.
> **Current remote code delivery:** Iterations 00–02 merged into `main`.
> **Current local candidate:** Iteration 03 economic-intelligence domain kernel; 23 new tests pass; not pushed.
> **Product name:** AwnNORA. `MyEconomy` is the repository/package implementation base.
> **Canonical system map:** `docs/AWNNORA_CONTEXT_MAP.md`.

## 1. One-sentence definition

Build a personal economic agency system in which every person can have a private AI representative to protect their interests, recover value, find opportunities, access benefits and resources, create income and operate a small enterprise; then, with explicit consent, those personal agents can coordinate through a collective economic intelligence network to unlock group opportunities and resources that individuals could not access alone.

## 2. Mission and positioning

**Mission:** Make individual people stronger from Day One.

**Positioning:** *Intelligence for the individual. Power for everyone.*

This is not merely a personal-budgeting app, cashback product, ad marketplace or chatbot for finance. Personal finance is an entry point into a wider personal economic operating system: it helps a person understand their position, defend their interests, discover and act on opportunities, mobilize resources and improve their economic agency.

The product must work for one person before a network exists. Commons is a multiplier, not a prerequisite for first-day usefulness.

## 3. Product experience: Personal Mode and Commons Mode

### 3.1 Personal Mode — valuable with one user

A new user should not need to connect five bank accounts, invite friends or wait for merchants to join. They can optionally provide a small amount of information, documents, goals, skills, availability and/or transaction data. The system returns a Personal Power Report with prioritized actions, evidence, confidence and what the user can do next.

A first-use experience can discover:
- possible money to recover or fees to challenge;
- recurring costs and obligations worth reviewing;
- protective actions against suspicious requests, hidden conditions or anomalous charges;
- potential scholarships, benefits, subsidies, concessions and reimbursements;
- work, projects, training, services and earning opportunities;
- knowledge or skills that can become paid services;
- small-business opportunities and the first steps to test them;
- a crisis action plan if income is disrupted or an unexpected bill appears.

Potential eligibility is not an award. A match is not a job. A projected saving is not realized saving. The interface must state these distinctions.

### 3.2 Commons Mode — the network-effect engine

Personal agents may share only narrow, purpose-specific signals with the Commons network after explicit consent. Commons can aggregate demand, match available supply and unused capacity, discover collective purchasing or bargaining power, and connect people with verified providers, institutions, funding and opportunities.

Potential network participants include people, households, workers, tutors, small businesses, suppliers, merchants, service providers, educational institutions, employers, NGOs and public/private programmes.

The network must not reveal raw financial transactions, exact personal circumstances or private capability records to other users or providers. Design for minimum cohort thresholds, suppression of rare attributes, anti-inference controls and auditable consent. A user must be able to use Personal Mode without contributing to Commons.

## 4. Full feature catalogue — the eight opportunity pillars

These are product pillars, not claims that the current codebase has implemented all of them.

### 4.1 Personal AI Representative / Guardian

Represents the user's stated interests in bounded workflows. It may identify possible duplicate or incorrect charges, overlooked refunds, warranty claims, compensation routes, recurring subscription changes, consumer-rights issues or contract changes; assemble evidence; draft requests; track deadlines and follow-ups; and prepare escalation artifacts. It must never invent legal rights, fabricate evidence or submit/agree to consequential actions without approval. Real complaint/provider integrations require verified endpoints, credentials, user authorization and jurisdiction-specific validation.

### 4.2 Opportunity Engine

Builds an optional user-controlled profile of skills, experience, portfolio, availability, location preferences and constraints. Matches it with jobs, freelance assignments, projects, tutoring, training, apprenticeships and other legitimate earning pathways. Supports applications, proposals, pricing, follow-up and outcome tracking. Do not promise employment or earnings.

### 4.3 Entitlement / Benefits Engine

Finds potentially relevant scholarships, public programmes, subsidies, concessions, grants, insurance reimbursements and employer benefits. Uses authoritative source material, versioned eligibility criteria, source dates and explainable rule evaluation. Distinguishes likely match, incomplete evidence, submitted application and confirmed benefit received. Official authorities/providers decide entitlement.

### 4.4 Resource Exchange

Matches underused human and commercial capacity with verified demand: available tutor hours, professional skills, equipment, tools, surplus inventory or produce, storage, transport capacity, seats, spaces, facilities and services. Requires listing verification, availability, pricing/terms, trust checks, booking or commitment state, cancellations and dispute handling.

### 4.5 Crisis Shield

Helps when a user faces income interruption, emergency medical/education/home expense or debt pressure. Reforecasts near-term cash flow, prioritizes essential obligations, identifies legitimate assistance and payment-relief routes, explores income opportunities and—only with consent—coordinates community support. It should not reflexively push loans, risky products or more spending.

### 4.6 Knowledge-to-Economic-Asset / Capability Graph

Turns demonstrable knowledge and skill into a user-owned, evidence-backed capability profile. Can connect the person with tutoring, consulting, mentoring, local services, micro-projects and knowledge exchange. It should support portfolio evidence, skill progression and reputation without claiming credentials the user does not have.

### 4.7 Economic Defence / Shield

Assesses suspicious messages, payment instructions, links, QR/payment requests, anomalous transactions, misleading contracts, hidden fees, unexpected recurring charges and scam indicators. Shows supporting evidence, confidence and safe next steps. A model suspicion is not proof of fraud; high-impact actions need human review and verified channels.

### 4.8 One-Person Enterprise Engine

Helps an individual move from skill or local demand to a small operating business. Includes demand discovery, validation, simple business model, startup budget, unit economics, pricing, catalogue/storefront, promotional content, customer enquiries, orders, invoices, supplier and delivery workflow, service operations and profit tracking. Payments, regulated activity and external commerce require authorized integrations and explicit user approval.

## 5. Financial foundation — the shared economic substrate

The product ultimately handles income, spending, recurring bills, EMIs, loans, tuition, healthcare bills, taxes, household obligations, budget envelopes, savings goals, assets/liabilities where relevant, affordability and cash-flow scenarios. It compares offers using full conditions and incremental costs rather than headline discounts.

Financial arithmetic, currency conversion, eligibility calculations, offer net-benefit calculation and verified-value accounting must be deterministic, tested and auditable. No LLM is the source of truth for monetary arithmetic. Different currencies are never summed without an explicit conversion rate, source, timestamp and method.

## 6. Collective Economic Intelligence Network — the killer move

The Commons network should transform isolated needs into collective bargaining and opportunity power.

Examples:
- Several households independently need the same education service. The network discovers aggregate demand and can seek a transparent group rate or sponsor-funded discount.
- Several people have complementary skills and availability; the system identifies a service team or a paid project opportunity.
- Local suppliers have unused capacity or surplus stock while nearby participants have matching demand.
- A local institution has unused facilities, equipment or seats that can be matched to verified community demand.
- A trusted sponsor funds a real user benefit in return for a transparent, eligible referral or service arrangement.
- A person in crisis can discover a legitimate relief opportunity or opt-in community support without publicly exposing private hardship.

Core technical concept: a **Collective Opportunity Graph** connecting needs, people/organizations, capabilities, resources, supply/demand, availability, location, offers, funding, evidence, permissions, commitments, transactions and outcomes. Individual records stay private; only specifically approved, protected aggregate signals enter network coordination.

The Commons must have real safeguards: minimum group thresholds, differential/aggregate disclosure controls where appropriate, membership and consent checks, abuse/fraud prevention, no re-identification, revocable participation, group commitment/cancellation semantics and transparent allocation rules.

## 7. Value creation, monetization and sharing

Revenue should come from value created, not from selling identifiable user financial histories. Potential models include merchant/provider referral or transaction commissions, sponsor-funded benefit programmes, booking/service fees, institutional subscriptions, employer/education partnerships, and research partnerships only where there is separate informed opt-in and lawful privacy-preserving design.

The user's proposed economic principle is to share **50% of clearly defined eligible net partner revenue** with users/participants and retain 50% at platform level, subject to precise contractual definitions. This is not 50% of gross impressions, gross merchandise value or uncollected amounts. Define attributable event, recognized revenue, refunds, taxes, processing costs, direct discounts and pass-through support separately. User rewards must be disclosed and auditable. Never incentivize invalid ad clicks or manipulate users into spending more.

Sponsored offers must be evaluated for genuine net user value: discount or funding minus additional spend, fees, shipping, lock-ins, quality compromises and conditions. Reject offers that reduce the user's actual welfare even when they pay a commission.

## 8. Verified Individual Value Created (VIVC)

North-star measure:

`VIVC = verified money recovered + verified expenditure savings + additional verified user earnings + benefits actually received + demonstrably prevented fees/penalties - additional costs incurred`.

Count an outcome only once, with baseline, evidence, provenance, verification status, timestamps and confidence. Keep potential opportunities, estimated value, attempted actions and verified realized outcomes in separate states. Supporting measures include time-to-outcome, successful completion rate, false-positive rate, user effort, quality of match, user control/satisfaction, fairness and privacy/security incidents.

## 9. Target architecture — logical system, not current implementation

The intended architecture uses strict modules in an initial modular monolith. Extraction into microservices is a later decision based on real load, deployment, team, isolation or reliability needs.

- **Personal Agent:** user-specific context, goals, skills, preferences, capabilities, authorizations and task history. Runs with scoped permissions.
- **MAKOS:** operational workspace and durable workflow surface for users/operators; shows tasks, evidence, states, approvals and outcomes.
- **GENIEA:** agent orchestration layer for mission planning, specialist-agent coordination, tool selection, bounded execution, retries and task resumption.
- **KRN:** knowledge/relationship graph for personal context and the Collective Opportunity Graph; strict private versus explicitly shared graph boundaries.
- **Data Plane:** transactional financial and user records, provenance, migrations, event/outbox, files and authorized integrations.
- **Knowledge/RAG Plane:** trusted retrieval over public rules, benefits, contracts, providers, product/service information and user-authorized documents. Retrieval is evidence, not authority for arithmetic or authorization. Store source/version/date and quote spans.
- **Logic & Intelligence Plane:** deterministic domain logic, rules, constraints, matching/ranking, forecasts, net-benefit optimization and outcomes; models assist interpretation and planning.
- **Agent & Automation Plane:** typed tools, durable state machines, checkpoints, replay/resume, idempotency, timeouts, retry budgets and human approval.
- **Orchestrator:** coordinates cross-plane workflows with traceable state transitions. It cannot bypass domain services, permissions or consent.
- **Meta AI/model layer:** use suitable Meta AI models and multimodal/reasoning capabilities for genuinely useful extraction, evidence understanding, interaction and agent planning; preserve provider abstraction and evaluate against task-specific baselines.

### Agent reliability principle

A 50-step workflow must not lose all progress because step 49 needs verification. Persist a durable mission state with completed steps, inputs/outputs, evidence, checkpoint IDs, tool versions, attempts, deadlines, pending approvals and compensation/reversal state. On interruption, resume from the last valid checkpoint; do not blindly repeat external side effects. Use idempotency keys and verify task state before retrying. Human verification should be requested only for the precise unresolved decision, not re-entered as context for the whole workflow.

## 10. Trust, privacy and safety invariants

1. Private by default; purpose-specific, revocable consent.
2. Collect the minimum information needed and define retention/deletion.
3. Strict user/household/tenant isolation at every data-access boundary.
4. Commons sees approved aggregates, never raw private transactions by default.
5. Every external source has provenance, timestamp and trust classification.
6. Retrieved content and user-supplied documents are untrusted input; resist prompt injection.
7. Tools have least privilege and typed input/output contracts.
8. Payments, contracts, applications, data sharing and other consequential operations require explicit scoped approval.
9. Record agent/tool action, policy checks, state change and external result in an audit trail.
10. Never claim a recommendation or model score is a verified outcome.

## 11. Demo strategy — make the final vision tangible

Use a single coherent synthetic household/person scenario. Demonstrate both live working functionality and clearly marked simulated/future components. A good story:

1. One person arrives alone; Personal Power Discovery shows immediate useful actions without Commons or bank integration being mandatory.
2. User-provided example data runs through deterministic financial calculations.
3. Guardian spots a potential billing issue, shows evidence, drafts a dispute and waits for approval.
4. Benefits/Opportunity engine identifies a sourced possibility and explains missing proof/next steps.
5. Personal Enterprise or capability graph converts a real skill into a plausible action plan.
6. A few opted-in synthetic users contribute privacy-limited demand signals; Commons produces a group opportunity.
7. A sponsor/provider offer is evaluated; an offer with misleading conditions or too much incremental spend is rejected.
8. A transparent ledger explains user value, realized versus estimated value, partner revenue and any user/platform share.
9. An unexpected expense arrives; the agent re-plans using durable checkpoints and requests only the necessary approval.
10. Close by showing the larger human economic opportunity network connecting individuals, resources, businesses, institutions and funding.

Demo rules: label synthetic data, mocked providers, simulated bids, estimated savings and future capabilities. Do not pretend a real refund, payment, award, partner agreement, transaction or network effect happened unless independently verified. Show system state, deterministic calculations, model/tool traces, provenance, approvals, and failure/recovery paths—not only a chatbot conversation.

## 12. Hackathon strategy context

The project is being shaped for a global Meta AI hackathon. The user's rubric as previously shared: real-world impact 30%, Meta AI tooling 25%, technical depth/execution 20%, demo 25%. Previously discussed bonus categories included viral reach, Meta open-weight model builds, community vote, agentic use case and creative build. Re-check current official rules and model eligibility before final submission; this section records prior planning context, not current rule verification.

Technical differentiators to demonstrate: privacy-constrained personal agents, deterministic economic optimization, collective demand intelligence, agent state persistence/checkpoint resume, multimodal evidence processing and a measurable user-value outcome. Do not add Meta tooling decoratively; make it essential to an actual user workflow and compare quality/latency/cost against a baseline.

## 13. Product identity and naming

**AwnNORA** is the confirmed project/product name for the Meta Global AI Hackathon. Preserve this exact casing. `MyEconomy` remains the existing repository and Python package name because it is the implementation base; it is not a competing product brand. Do not reopen naming or propose alternatives unless the user explicitly asks. `MAKOS`, `GENIEA` and `KRN` are named architectural systems within AwnNORA, not alternate product brands.

## 14. What is implemented today (reconcile with PROJECT_STATUS.md)

### Iteration 00 — deterministic calculation foundation
- Python 3.12/3.13 FastAPI application with Pydantic contracts and health/readiness.
- Pure `Decimal` cashflow calculation over caller-supplied entries, using a curated currency precision registry.

### Iteration 01 — identity, household trust and consent
- SQLAlchemy/Alembic persistence for users, email challenges, opaque sessions, households, invitations, consent grants and audit events.
- Argon2id password hashes, digest-only session/verification tokens, verified-email gates, owner-only invitation controls and revocation.
- Purpose/category/recipient-specific consent; Commons and research cannot request raw transaction/contact/evidence categories.
- Append-only audit events protected at ORM and database-trigger layers.

### Iteration 02 — financial data plane v1
- Persisted user-owned financial account metadata, import batches, transactions and recurring obligations.
- Monetary storage as integer minor units (`BIGINT`) plus currency code. No float arithmetic and no cross-currency aggregation or implicit FX.
- Composite database constraints bind each transaction/import/obligation to the same account owner; transaction and obligation currencies must match the linked account.
- Bounded 2 MiB / 10,000-row CSV ingestion; strict UTF-8/header/date/Decimal/direction/treatment/status/category checks; 32-column cap; unknown header columns tolerated, duplicate normalized header names rejected.
- Import provenance: byte-level SHA-256 source hash, sanitized filename, owner-scoped idempotency key, batch state/counters, validation errors and audit events. Original uploaded file bytes are never retained.
- Provider external references are unique per owner/account. Same reference + same financial fingerprint is skipped only when lifecycle state is unchanged; same reference + changed economic content rejects the batch atomically. Provider state can progress only through audited monotonic transitions (`PENDING -> POSTED|REVERSED|VOID`, `POSTED -> REVERSED|VOID`); terminal states cannot be reactivated. SQLite/PostgreSQL database guards enforce financial-fact immutability and the monotonic provider status state machine in addition to application logic. Only a missing `posted_at` value may be filled; existing transaction facts cannot be rewritten.
- A missing `cashflow_treatment` is conservatively stored as `IGNORE`, not inferred from CREDIT/DEBIT alone; `amount_inr` cannot be imported into a non-INR account.
- Similar rows without a provider reference are preserved and linked as possible duplicates rather than silently dropped; they require review.
- Only `POSTED` records are included in persisted cashflow. `PENDING`, `REVERSED` and `VOID` are excluded. `TRANSFER`/`IGNORE` do not affect income/expense. `REFUND` offsets expenses, not income. The displayed ratio is named `net_cashflow_to_income_percent`, not verified savings.
- Account, transaction, import-batch and recurring-obligation APIs are owner-scoped. Non-owner access returns 404. Household membership is not used as a financial-data permission.
- `scripts/seed_synthetic_customer.py` loads one synthetic persona into an existing, active, verified local user only; it refuses production mode, creates no fake login identity and uses deterministic idempotency/source IDs.

### Iteration 03 — AwnNORA economic-intelligence domain kernel (local candidate)
- `domain/economic_intelligence.py` adds deterministic invoice/evidence review, offer net-value evaluation, consent-aware Commons demand aggregation, strict VIVC accounting, GENIEA mission transitions and tool-authorization gates.
- `tests/test_economic_intelligence.py` adds 23 focused tests. The complete local suite passes 79 tests.
- These are domain primitives only. No Guardian document API/vault/OCR/model extraction, persisted case state, durable GENIEA runtime/checkpoint, KRN graph persistence, live Commons service or MAKOS UI exists yet.

The Iteration 02 CSV/API flows are merged into `main` through PR #2 at `a55cb388ef7baf72766e2fcabe89f0dee1c45979`. Its GitHub Actions run `41801123405` passed Python 3.12, Python 3.13 and PostgreSQL 16 service-backed migration/audit checks. Iteration 03 remains a local-only domain kernel until its own branch/PR is created and CI passes.

### Still designed / not yet implemented
No live bank aggregator, official bank-data consent integration, statement provider connectors, encrypted document vault, category-learning service, budgets/goals/forecast engine, benefits rules catalogue, Guardian claims flow, opportunity marketplace, resource exchange, crisis workflows, enterprise operations, Commons aggregation engine/anti-inference controls, offer optimizer, VIVC evidence ledger, partner commission/payout engine, RAG, graph runtime, durable agent/checkpoint engine, Meta model gateway or production deployment exists yet. Synthetic records for these future capabilities remain fixtures only. Use `docs/FEATURE_CATALOG.md` and `docs/PROJECT_STATUS.md` as the status authority.

## 15. Hackathon judging and model policy context

The project owner supplied a working rubric of real-world impact (30%), Meta AI tooling (25%), technical depth/execution (20%) and demo (25%), plus bonus targets for viral reach, open-weight model build, community vote, agentic use-case and creative build. Treat the weights and bonus specifics as participant-provided until confirmed in the current official entrant rules.

The official Meta Global AI Developer Hackathon page currently lists submissions due November 4, 2026 at 9:00 PM ET, judging November 4–8 and a November 9 closing ceremony; verify the portal again before final submission. Meta's current geographic policy identifies India as restricted for Muse Image. Contributor Services must not receive sensitive, confidential or personal information; use Standard Services for permitted personal-information processing or process locally with suitable open weights, and use synthetic data in the demo. Muse Glimmer is a candidate open-weight local agent model; no Meta model has been integrated in the current code yet. Full model/bonus notes and source links are in `docs/HACKATHON_SCORECARD.md`.

## 16. Source-of-truth hierarchy

When sources disagree, use this order:

1. Latest explicit user-confirmed product decisions and `docs/AWNNORA_CONTEXT_MAP.md` for project identity and intended system boundaries.
2. Current code, tests, migrations and live repository state for what is implemented.
3. `docs/PROJECT_STATUS.md` for dated implementation status, reconciled against code.
4. Feature specs and ADRs for approved design decisions.
5. This project memory for overarching product intent and constraints.
6. Prior chat history for unresolved ideas only; update this repository when the user confirms a decision.

Never claim persistent model memory just because this file exists. At the beginning of each future engineering session, read the repository's current memory documents and inspect the current branch/HEAD.

## Synthetic Demo Dataset v1 (2026-11-03)

A deterministic synthetic fixture corpus now lives at `demo_data/synthetic_v1/`. It models 120 fictional adult customers, 55 households, 42 entity tables and 17,425 rows across financial records, transactions, obligations, loans, bills, subscriptions, consents, benefits, capabilities, opportunities, offers, resource listings, Commons signals/campaigns, Guardian cases, risk/crisis records, micro-enterprises, orders, agent missions/checkpoints, settlements and audit events. It includes CSV, JSON, JSONL, PostgreSQL DDL/seed, SQLite and synthetic HTML/PDF/PNG source documents. `README.md`, `docs/DEMO_PLAYBOOK.md` and `docs/SYNTHETIC_DEMO_DATASET.md` describe exact usage and boundaries.

`CAM00001` is a 5/5 Commons quorum fixture with five fictional participants whose purpose-specific demand consent is valid at signal time. It uses a matching simulated Jaipur education offer; no provider quote, fulfilment, sponsorship or payout is real. Other campaign rows without a matching offer remain in gathering state. The dataset is a test fixture and never a real customer base or measured impact. VIVC rows carry `SYNTHETIC_FIXTURE_ONLY`.

The regulatory mapping records India-oriented engineering controls for DPDP staged commencement, RBI Account Aggregator and conditional Digital Lending requirements. It is not legal advice or a compliance claim. Re-check official commencement and applicable regulatory roles before production.
