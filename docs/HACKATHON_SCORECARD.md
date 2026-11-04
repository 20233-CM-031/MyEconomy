# Hackathon Strategy Scorecard

**Purpose:** Turn the judging rubric supplied by the project owner into engineering and demo acceptance criteria.
**Last verified against public event/model sources:** 2026-11-03. Implementation status reconciled to repository on 2026-11-04.
**Important:** The exact scoring weights and bonus award details below are the participant-provided rubric. Re-check the accepted-participant Official Rules and submission portal before relying on every bonus condition.

## 1. Judging rubric supplied by the project owner

| Category | Weight | Evidence judges need to see | Product response |
|---|---:|---|---|
| Real-world impact | 30% | Clearly harmed/underserved users, importance, actual user benefit and plausibility of real use | Personal Power Discovery works before the network exists; Guardian/Benefits/Opportunity workflows focus on measurable actions and outcomes. Commons multiplies value as participants grow. |
| Meta AI tooling | 25% | Meta models are essential to the product, not a logo/API wrapper; strong model choice, multimodal use and evaluation | Make model capabilities solve concrete tasks: extract and structure evidence, interpret confusing documents/offers, plan tool workflows, recover from interruptions. Show exact model, real tool traces and comparison to a baseline. |
| Technical depth and execution | 20% | Correct architecture, robust systems, thoughtful design, implementation quality and refinement | Deterministic finance core, strict identity/consent boundaries, migrations, typed APIs, tests, audit trail, durable agent checkpoints, privacy-preserving Commons and reproducible deployment. |
| Demo | 25% | Product visibly works; clear narrative and compelling proof | One coherent synthetic-user story with live endpoints, real state transitions, model/tool trace, approval gates, failure/recovery and a verified-value ledger. Label simulations. |

## 2. Product thesis to tell judges

**Make individual people stronger.** Each person starts with a private AI representative that helps defend their interests, recover value, find opportunities and turn capabilities into income. As people opt in, their agents can safely coordinate demand and resources to create collective economic power unavailable to isolated individuals.

The product is not just a finance tracker, budget chatbot, cashback portal or ad network. The technical thesis is that autonomous personal agents can transform private needs and capabilities into purpose-limited, privacy-preserving opportunity signals, then coordinate real actions under explicit user control.

## 3. Feature-to-impact scorecard

| Feature | Immediate value for 1 user | Value with a few users | Final network-scale value |
|---|---|---|---|
| Personal AI Representative / Guardian | Review a bill, identify a possible error, assemble evidence and draft the user's next action | Shared templates and verified provider patterns, without exposing case details | Users supported at scale by trusted, evidence-grounded workflows |
| Opportunity Engine | Match skills, time and constraints to a real next step | Cross-match projects, mentors and demand | A broad capability-to-opportunity graph |
| Benefits / Entitlement Engine | Discover a possible benefit and prepare documents | Trusted referrals and shared non-sensitive guidance | Higher awareness and completion of support pathways |
| Resource Exchange | Find an available service/resource | Match unused capacity with a few real requests | Local and cross-region capacity marketplace |
| Crisis Shield | Reprioritize commitments and identify legitimate relief | Voluntary support/resources coordinated by consent | Resilience and safer crisis coordination |
| Knowledge-to-Economic-Asset | Package one demonstrated skill into a service offer | Match tutors, learners and service requests | Distributed human capability economy |
| Economic Defence | Explain suspicious requests and risky terms | Share anonymized patterns/indicators with guardrails | Wider defensive intelligence without exposing personal accounts |
| One-Person Enterprise | Validate demand and build a small operating plan | Find early buyers/suppliers and shared services | Agent-assisted microenterprise formation/operations |
| Commons | No dependency on Commons for the first result | Consent-based aggregated demand and provider matching | Collective purchasing, resource and opportunity intelligence |

## 4. Meta model strategy — meaningful and privacy-aware

### Preferred model roles to evaluate

- **Muse Glimmer (open-weight, local):** candidate for private/local document understanding, user-context reasoning and the bounded personal agent loop. Meta's documentation describes it as a 30B multimodal open-weight model with local deployment, tool use and long-running agent capabilities. We must benchmark it on the actual available hardware and actual tasks; do not claim it runs locally until a verified runtime test exists.
- **Muse Spark / Muse Wonder (Meta Model API Standard Services):** candidate for high-complexity planning, multi-step orchestration, multimodal interpretation or public-information research where a hosted model materially improves the result. Keep model calls behind a provider abstraction and typed tools. Use Standard Services for any permitted workload involving personal information.
- **SAM 3.1:** optional image/video segmentation for tasks where region-level localization is genuinely needed (e.g., identifying and isolating receipt line items). It is not required for the first trust iteration; benchmark accuracy and benefit before adding it.
- **Muse Image:** do not use for this India-based project. Meta's current geographic policy lists India as a model-specific restricted location for Muse Image. Do not attempt to bypass geographic controls.
- **Muse Wonder for creative build:** candidate if it is confirmed eligible in the official bonus rules and accessible through the team's account. Creative use must support the product (e.g., personalized explainers or visual opportunity plans), not be a decorative unrelated generation.

### Data-tier safeguards

Meta's Contributor Services policy says not to submit sensitive, confidential or personal information to Contributor Services; Standard Services should be used where personal information is processed. Never send actual user financial histories, identifying documents or confidential records to a Contributor endpoint or Contributor-mode coding harness. Prefer synthetic demo data. For local personal workloads, evaluate Muse Glimmer on-device and keep user data within the local trust boundary wherever possible. Re-check the model designation and terms on the day of submission because Meta may change availability/designations.

### What a genuine Meta integration must demonstrate

1. The model is named explicitly, with exact model ID/version and service tier.
2. The input is appropriately authorized, minimized or synthetic.
3. The model performs a meaningful capability: image/document understanding, structured extraction, reasoning/planning or a constrained tool decision.
4. Outputs are schema-validated and checked by deterministic business rules.
5. Model failures, malformed tool calls, timeout and uncertainty have tested behavior.
6. Compare quality, latency and cost against a transparent baseline.
7. Show real traces in the demo; never simulate a Meta response or imply an uncalled model was used.

## 5. Bonus-prize targets supplied by project owner

| Award | Prize | Target strategy | Submission evidence / caution |
|---|---:|---|---|
| Most Viral Project | $20,000 | Share a striking, understandable Personal Power Report and a short demo of a real user outcome | Publish actual demo on X and submit its URL, as described in the participant-provided rubric. Use only synthetic or explicitly authorized material. |
| Best Meta Open Weight Model Build | $10,000 | Make Muse Glimmer a real local agent capability, or use an eligible Muse Spark Open release as a core model | Show model weights/runtime, measured tool-use loop, local data boundary, benchmark, failure recovery and model-specific contribution. Confirm official award eligibility. |
| Community Vote | $10,000 | Design a clear public gallery page and a simple shareable story | Provide a direct gallery submission and ethical vote/share campaign. Verify official public-voting rules. |
| Best Agentic Use-Case | $5,000 | Demonstrate a multi-step mission with durable checkpoints, typed tools, approvals, retries and recovery | Show the task state and prove that resumption does not repeat a completed side effect. Use actual model-generated tool selection where applicable. |
| Best Creative Build | $5,000 | Create a product-native visual explanation of a person's possible value/opportunity journey | The owner-provided notes mention Muse Image or Muse Wonder. Muse Image is restricted from use in India under Meta's current policy; evaluate Muse Wonder only if it is eligible and available under official rules. |

These amounts and special award conditions are recorded from the project owner's supplied judging notes. The public hackathon overview independently confirms a $1M total prize pool, indie and startup tracks, the use of Muse Spark, Muse Image, SAM 3.1, Meta open weights and Muse Code. The specific bonus award rules must be verified from the official participant rules/submission portal.

## 5A. Iteration 02 contribution to the rubric

The financial data plane moves the demo from pure caller-provided calculations to a persisted, owner-scoped user record. It supports a real API sequence for a single verified local user: create account metadata, import a bounded synthetic statement, inspect the import hash/outcome, list transactions, and compute posted-only cashflow. The importer enforces minor-unit money, currency matching, conservative unclassified treatment, idempotency, provider-reference conflict detection, monotonic pending/posted/reversed lifecycle reconciliation, database-level status-transition guards, atomic rejection and audit metadata. This is concrete technical-depth evidence and a more realistic substrate for the Personal Power/Guardian story. It does **not** yet produce a verified real-world user outcome and it does not integrate a Meta model; those remain the next engineering objectives.

## 6. Demo blueprint — one to three synthetic users

Use a single story, not eight disconnected feature demos.

1. **Day One, one user:** A person signs up, verifies email, provides a small synthetic household profile and asks for help finding one immediate economic improvement. The Personal Power Discovery concept is explained; only currently implemented functionality is labelled live.
2. **Protection:** User submits a sample invoice/bill. A model (when integrated) extracts line items and terms; deterministic checks calculate totals and compare known inputs. The Guardian presents a potential issue with source/evidence and asks approval before preparing an external action.
3. **Capability and support:** The Opportunity/Benefits engines show a grounded match or a clearly labelled future integration. Eligibility is “possible” until an authoritative process confirms it.
4. **A few users:** Two or three synthetic people separately grant purpose-specific Commons consent. Show that household membership does not grant finance access and that raw transactions/contact details are not sent to Commons under the current consent policy.
5. **Collective result:** The system aggregates allowed signals, evaluates a synthetic provider offer, calculates net value and rejects any offer that induces more spending or worse conditions than the benefit.
6. **Agent reliability:** Introduce a changed constraint (unexpected bill, unavailable provider, or revoked consent); show a checkpointed mission resume/replan and human approval boundary.
7. **Value proof:** Report recovered amount/savings/earnings/benefits as verified only when evidence confirms them. Keep estimates and simulated partner bids separate.
8. **Final vision:** Visualize the wider network: individuals, skills, demand, resources, providers, institutions and community support connected through private agents and privacy-controlled signals.

### Demo truth labels

Every feature must be labelled `LIVE`, `SIMULATED`, `PLANNED` or `EXTERNAL / NOT CONNECTED`. Do not present mocked partners, fake payments, invented savings or synthetic network results as real outcomes.

## 7. North-star evidence

`VIVC = verified money recovered + verified expenditure savings + additional verified user earnings + benefits actually received + demonstrably prevented fees/penalties - additional costs incurred`.

For each outcome show: user baseline, evidence reference, outcome state (`estimated`, `attempted`, `pending`, `verified`, `rejected`), currency, time and verification method. Do not add an opportunity estimate to VIVC.

## 8. Current scorecard status

| Judging area | Current implementation status | Next evidence required |
|---|---|---|
| Real-world impact | Product vision and user-first architecture documented; cashflow/trust foundations work, but no live customer outcomes yet | Implement first useful personal workflow and measure a genuine, consented result |
| Meta AI tooling | **Not integrated yet** | Select model(s), make one essential task work end-to-end, test errors and compare against baseline |
| Technical depth | Iterations 00–02: modular monolith, identity/consent, deterministic cashflow, minor-unit ledger, owner/currency composite constraints, import idempotency/provenance, monotonic audited provider-status transitions, database-enforced transaction financial-fact immutability and monotonic status-transition guards and synthetic fixture seeder | Run Iteration 02 PostgreSQL CI, concurrency tests, production hardening, durable agent workflows and integration contracts |
| Demo | Live API and trust flow can be demonstrated with local email adapter and synthetic users | Build polished end-to-end UI, model traces, VIVC ledger and final-vision visual; label simulations |
| Open-weight bonus | Muse Glimmer not integrated/runtime-tested | Local inference runtime, model tool loop, evaluation and resource measurements |
| Viral/community bonus | Not implemented | Public-safe share artifact, gallery entry, X post and rule-compliant voting plan |
| Agentic bonus | Agent runtime not implemented | Durable mission state, checkpoint/resume, idempotent tools and successful recovery demo |
| Creative bonus | Not implemented | Confirm eligible model, create product-native visual output and integrate into user journey |

## 9. Time-critical event information

The public Meta Global AI Developer Hackathon page lists project submissions due **November 4, 2026 at 9:00 PM Eastern Time**, judging November 4–8 and closing ceremony November 9. On November 4, 2026, Eastern Time is EST (UTC-5); that corresponds to **November 5, 2026 at 7:30 AM India Standard Time**. Confirm the submission portal's displayed deadline immediately before submission in case organizers change it.

Official references:
- Event overview and dates: https://dev.meta.ai/events/global-hackathon
- Meta Model API model/geographic policy: https://dev.meta.ai/legal/geographic-use-policy
- Contributor tier rules: https://dev.meta.ai/help/policies-and-privacy/contributor-tier
- Muse Glimmer model and license: https://dev.meta.ai/docs/muse-glimmer
- Meta Model API terms: https://dev.meta.ai/legal/terms-of-service
- Muse Wonder model documentation: https://dev.meta.ai/docs/models
