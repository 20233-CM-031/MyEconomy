# Project Memory — MyEconomy / Future Brand TBD

> **Purpose:** Durable project context for future engineering sessions, contributors and AI coding assistants. This is the canonical high-level memory of the product's intent, architecture, constraints and decisions. It must be updated when decisions or capabilities change.
>
> **Last reconciled with source tree:** 2026-11-03.
> **Current code delivery:** Iteration 00 — deterministic cashflow API foundation.
> **Product brand:** Not selected. Repository remains `MyEconomy`.

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

These are product pillars, not claims that Iteration 00 has implemented them.

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

## 13. Naming and brand decision

The final product name is **not selected**. `MyEconomy` is the repository and working project name. The user asked for a lively, modern, memorable name and explicitly rejected Sanskrit-derived and Christian/religiously coded naming directions. Do not presume that Arabic-rooted naming is required or that a suggested name is approved. AWNORA was suggested as an option but is **not approved**; do not use it as the current brand. Any future shortlist needs pronunciation, meaning, unwanted associations, search-result collision, domain, app-store and trademark screening before adoption.

## 14. What is implemented today

Only the Iteration 00 slice is implemented in the current source tree: Python/FastAPI service, health endpoints, request/response schemas and an in-memory, deterministic calculation over caller-supplied entries. It uses `Decimal`, a curated currency exponent registry, period checking, essential/discretionary aggregation, category aggregation and a net-cashflow/income ratio. Automated tests and a local HTTP smoke test were recorded as passing.

There is no database, identity system, consent ledger, bank connection, transaction importer, agent runtime, RAG, graph store, Commons network, merchant integration, benefits API, claims integration, payment or deployed customer workflow. The target architecture and feature catalogue must never be confused with implemented code.

## 15. Source-of-truth hierarchy

When sources disagree, use this order:

1. Current code, tests, migrations and live repository state for what is implemented.
2. `docs/PROJECT_STATUS.md` for dated implementation status, reconciled against code.
3. Feature specs and ADRs for approved design decisions.
4. This project memory for overarching product intent and constraints.
5. Prior chat history for unresolved ideas only; update this repository when the user confirms a decision.

Never claim persistent model memory just because this file exists. At the beginning of each future engineering session, read the repository's current memory documents and inspect the current branch/HEAD.
