# AwnNORA Vision → Engineering Delivery Matrix

This is the implementation map that prevents the complete product vision from becoming a disconnected collection of agents or dashboards. It identifies what exists in the current repository and the next complete vertical slice required for each capability.

## 1. One system, not six unrelated products

The common object is a **Personal Economic Case**: a typed, owner-scoped problem or opportunity with a goal, facts, constraints, evidence, permissions, options, next action, approvals and eventual outcome. Engines contribute findings and actions to that case. MAKOS presents it; GENIEA runs bounded work; KRN stores context and provenance; deterministic domain services protect economic truth.

Every case should expose:

- who owns it and which household/organization scope applies;
- what the user wants to improve or protect;
- which source facts and evidence support each finding;
- what is unknown, stale, inferred or low-confidence;
- options ranked by user benefit after costs and constraints;
- the exact next step, owner and deadline;
- whether an action is proposed, approved, attempted, acknowledged, settled or verified;
- any direct user cost, partner revenue and eligible user/platform share;
- a full audit timeline and exportable evidence packet.

## 2. Capability-by-capability truth and build contract

| Vision engine | Current repository truth | Complete engineering slice still required | Synthetic demonstration story |
|---|---|---|---|
| Personal Mode / Household Economic Twin | Identity, consent, accounts, CSV imports, posted cashflow and recurring obligations are persisted. Iteration 05 overlay adds a read-only Power Report candidate. | Progressive intake; verified data coverage; time-aware income/obligation/goal model; explainable priorities; user task and outcome tracking; consent-aware data readers. | A single user gets a private report without bank linking, identifies a bill/duplicate candidate, chooses a next action and sees the state change only after evidence. |
| Guardian / Economic Defence | Evidence upload and invoice review exist, but files remain `STORED_UNSCANNED`; structured values are caller-supplied; draft approval means manual user delivery only. | Quarantine and real malware scan; parser sandbox; OCR/model extraction with page/region spans; locator/hash verification; invoice/contract/recurring-charge rules; dispute packet; user-controlled escalation; refund reconciliation. | Price jump, line arithmetic mismatch, duplicate invoice, low confidence, injected prompt, spoofed MIME and rejected/unavailable scanner. |
| Opportunity Engine | Skills, opportunities and match fixtures exist; no complete application service or live demand source. | Evidence-backed capability graph; availability and user constraints; verified demand source; gross-to-net income calculation; safety/quality/terms evaluation; proposals and user opt-in; paid outcome confirmation. | Tutor availability matched to a verified request; low-quality job rejected despite headline pay; artisan portfolio gap clearly shown. |
| Entitlement Engine | Fictional benefit catalogue and assessment/application fixtures exist; no official eligibility engine. | Versioned authoritative-source registry; jurisdiction/time-specific rules; deterministic eligibility constraints; missing-document checklist; deadline tracker; application pack and status polling through authorized channel; award confirmation. | Potential scholarship match with missing proof; stale scheme source abstains; no fixture may appear as an official award. |
| Resource Exchange | Resource listing/demand fixtures exist; no persistent live exchange. | Trusted listing; capacity/time/location/safety constraints; identity/party checks; both-party confirmation; commitment, cancellation, refund/dispute and fulfilment state. | Empty teaching seats, unused equipment or expiring surplus produce match to need; both parties confirm before commitment. |
| Crisis Shield | Crisis and risk fixtures exist; no complete persisted triage runtime. | Shock intake; essential-needs ordering; due-date prioritization; reversible spending controls; validated relief/grant/benefit routes; hardship/moratorium path; crisis-safe earning; human review and crisis escalation. | Salary delay + rent/food; medical shock; multiple EMI pressure; no automatic new-loan recommendation. |
| One-Person Enterprise | Micro-enterprise, products and simulated orders exist as data; no operational business back office. | Full unit economics (materials, labour/time, wastage, packaging, delivery, fees, tax); pricing floors; catalogue; quote/order state; invoice/receipt; payment reconciliation; tax exports and customer communications. | Baker/repair technician/tailor turns costs and capacity into a profitable draft quote/order; below-cost offer is blocked. |
| Commons / Collective Opportunity | Economic-intelligence kernel includes an in-memory consent-aware aggregation primitive; static five-person quorum fixture exists. No persistent exchange or verified partner. | Persistent purpose-bound contributions; event-time consent; privacy budget/query governance; anti-differencing; cohort suppression; supplier validation; complete net-benefit optimizer; negotiation; cancellation; escrow/payment/settlement; 50/50 eligible net revenue ledger. | Five opted-in households unlock a hypothetical education procurement candidate; raw records remain private; harmful offer is rejected; no real quote/payout is implied. |
| GENIEA | Mission transition/tool authorization primitives exist in the domain; no durable worker/executor. | Persisted mission and step state; leases; checkpoints; bounded tools; retries; outbox; human approval; cancellation; replay/reconciliation; tool/model cost and trace; permission revocation checks. | A late failure resumes from last valid checkpoint without replay; provider timeout reconciles before another attempt; revoked approval blocks mutation. |
| KRN | KRN/GENIEA architecture proposal exists in docs; no production graph/knowledge runtime. | Typed private fact/evidence/relationship stores; temporal validity; provenance and hash-addressed spans; retrieval; conflict/staleness handling; explicit shareable-edge projection; retrieval evaluation and privacy tests. | Stale rule source is rejected; evidence span with wrong document hash is denied; private household edge is invisible to Commons. |
| MAKOS | No dedicated product workspace UI yet. Existing FastAPI docs are developer surfaces. | User onboarding; Power Report; personal case inbox; case/evidence timeline; task and approval center; mission status; value ledger; Commons controls; settings/data export; responsive accessible UI. | First-user journey from account setup → report → evidence/case → approval choice → outcome status, with synthetic/sandbox/live labels. |
| VIVC / Value Settlement | Deterministic VIVC domain primitive exists; static events are synthetic; no production outcome ledger. | Persistent lifecycle; evidence and baseline; settlement/provider confirmation; duplicate/idempotency constraints; costs/fees/taxes/refunds; currency-safe aggregation; user statement and payout reconciliation. | Estimate stays estimated; provider acknowledgement stays pending; only evidence-backed settled live outcomes count once. |
| External money / sustainable platform economics | Revenue share is a product proposal; no settlement engine or partner contracts. | Commercial eligibility and disclosures; merchant direct discounts; earmarked sponsor/grant pass-through; referral commission contract; eligible net-revenue definition; tax/refund/chargeback treatment; user share and payout ledger. | User gets full direct discount/subsidy; referral commission is split only when received and eligible; no paid ad clicks or sale of identifiable bank records. |

## 3. The first-user path is the critical spine

The first user should not wait for Commons, an agent swarm or a bank partnership. The minimum journey is:

1. Create account and verify control of the email inbox.
2. Explain personal-data use and allow manual context/import; bank linking is optional.
3. Bring in records with source, period and currency; show incomplete/unclassified records explicitly.
4. Build the Personal Power Report with deterministic calculations and source-linked findings.
5. Let the user open one finding as a case, add supporting evidence, choose an action and approve any communication.
6. Track attempt, external acknowledgement and final verified outcome separately.
7. Update VIVC only after settlement/evidence rules are satisfied; otherwise keep it at zero/pending.

The delivered Iteration 05 slice implements steps 1–4 for the existing synthetic financial persona (and steps 1 and 3–4 can be exercised with an existing local verified account). Steps 5–7 are the next product slices; do not present the report alone as proof that the user recovered money or earned new income.

## 4. Demo data should be generated from the same contracts as the software

Use three separate fixture layers:

- **Relational persona corpus:** `demo_data/synthetic_v1/` — household, account, transaction, obligation, bill, benefit, skills, enterprise, Commons and agent records. This is the realistic cross-table population.
- **Document corpus:** synthetic HTML/PDF/PNG invoice and fictional terms. Each file has a digest and known expected field spans. Add malformed, adversarial and corrupted variants only as non-executable isolated test fixtures.
- **Scenario/event corpus:** `demo_data/scenario_lab_v1/` — explicit scenario run records with deterministic expected decisions, event order, idempotency and invariants.

Every scenario template should be paired with (a) valid/happy case, (b) boundary case, (c) abuse/invalid case, (d) dependency failure, (e) retry/replay case and (f) recovery/compensation case. A fixture is promoted to an application acceptance test only after it runs through the real target service/API and checks persisted state.

## 5. How to measure whether the vision is becoming real

Do not optimize only for number of agents, prompts, models or screens. Track:

- time from signup to first useful evidence-backed action;
- share of findings with correct source/provenance and calibrated abstention;
- false-positive and missed-case rate by capability;
- action completion and provider settlement/reconciliation rate;
- independently verified net VIVC per user, with synthetic/sandbox excluded;
- net income unlocked after time/material/platform costs;
- essential-bill burden and avoidable fees demonstrably reduced;
- mission resume success without duplicate side effects;
- consent withdrawal propagation latency and privacy/security incidents;
- user approval comprehension, reversals, complaints and trust.

The objective is not to maximize AI autonomy. It is to make the user materially stronger while keeping truth, control and economic accountability intact.
