# AwnNORA — Turbo Parallel Engineering System

## 1. The two-ended delivery method

AwnNORA advances from both ends and converges at executable contracts.

**Forward engineering starts at a real person's outcome:**

`User intention → MAKOS journey → Personal Economic Case → GENIEA mission → typed service command → deterministic rule → persisted evidence/state → confirmed external response → VIVC`

**Reverse engineering starts from scenario and evidence:**

`Synthetic scenario → expected decision/invariants → domain contract → service/API → persistence and audit → UI event → observed output → evaluator`

A feature is not complete because a screen renders or a synthetic fixture says `PASS`. It is complete when the same business contract is exercised through domain, persistence, API and user interface, including negative paths and recovery.

## 2. Shared system contracts

All parallel workstreams use these stable concepts:

- `PersonalEconomicCase`: owner and scope, goal, facts, constraints, evidence, unknowns, permissions, ranked options, next action, approvals, timeline and outcome.
- `EvidenceReference`: source digest, locator/span, observed value, source class, extractor/version, confidence, timestamp and verification state.
- `EconomicAmount`: integer minor units + ISO currency + source + effective time. Never floating-point.
- `ConsentScope`: subject, purpose, categories, recipient, terms version, expiry and revocation. Enforced at the actual data read or external operation.
- `Mission`: immutable intent, owner, execution environment, tool permissions, plan version, checkpoint, deadline, idempotency and cancellation/reconciliation state.
- `Outcome`: proposed → attempted → acknowledged → settled → verified, with evidence, baseline, costs, currency and idempotency.
- `Environment`: `SYNTHETIC`, `SANDBOX`, `LIVE`. Adapters reject a request/environment mismatch.

## 3. Parallel workstreams

| Workstream | Ownership | First complete vertical slice | Integration gate |
|---|---|---|---|
| P0 — System integration | Architecture contracts, repo status, typed API conventions, test matrix | contract registry, CI matrix, feature-status reconciliation | no subsystem bypasses consent, audit, money or environment gates |
| P1 — MAKOS Web | TypeScript app shell, onboarding, Power Report, case inbox, permissions, responsive design | login → private report → finding → read-only case view | live API mode is authenticated; demo mode has no external network path except local health |
| P2 — Personal + Guardian | Personal Economic Case, evidence trust pipeline, OCR provenance, dispute packet | safe document upload → scan → extract → deterministic review → human draft | quarantined/failed documents never reach OCR or model |
| P3 — GENIEA | durable mission state, worker leases, event/outbox, retry, checkpoints, approvals | long-running read-only investigation with interruption/resume | replay-safe side effects; approval hash/scope/revocation checked at execution |
| P4 — KRN | typed private facts/evidence/edges, temporal validity, provenance, retrieval and conflicts | source-backed evidence retrieval for one Personal Economic Case | hash/locator validation; private partition cannot be read by Commons |
| P5 — Economic engines | Opportunity, Entitlements, Crisis Shield, Resource Exchange, Enterprise, Commons | one coherent opportunity/benefit/resource flow with net economics and human approval | source freshness, eligibility, quality, consent, net benefit and counterparty state |
| P6 — Scenario/evaluation | synthetic personas, documents, event traces, failure injectors, model benchmarks | every acceptance story runs against the actual target services | 100% invariants pass; actual code outputs compared to expected results |
| P7 — Deployment/operations | PostgreSQL, queue, object storage, secrets, metrics/traces, recovery | repeatable local/staging launch and recovery runbook | backup/restore, health, alerts, worker restart and environment separation verified |

Parallel contributors own separate file areas and migrations. A single integrator approves cross-boundary changes. Shared schemas are changed through a short contract proposal before code diverges. Do not have multiple contributors editing the same migration, consent policy, money kernel or status documents concurrently.

## 4. Engineering dependency order

1. Freeze the first shared data model: case, evidence, consent, mission, event and outcome.
2. Deliver MAKOS shell over the existing identity, financial and Personal Power APIs.
3. Implement Guardian quarantine/scanning before multimodal extraction.
4. Add model gateway and source-grounded extraction against synthetic documents, then calibrate abstention and evidence spans.
5. Add persistent GENIEA mission execution, leases/checkpoints/outbox and user approvals.
6. Add KRN provenance and temporal/visibility boundaries.
7. Implement one Opportunity + Entitlement + Crisis/Economic Defence journey using source-versioned rules.
8. Add resource/enterprise flows and then persisted Commons aggregation + net settlement.
9. Run the complete scenario suite through APIs, UI and failure recovery.
10. Move synthetic → sandbox → internal pilot → partner pilot only when release gates pass.

## 5. Definition of done

- Domain invariants, typed request/response contracts and state transitions are explicit.
- Migration upgrade/downgrade works on SQLite and PostgreSQL.
- Tests include happy, boundary, invalid, authorization, cross-tenant, concurrency, timeout, idempotency, retry, replay and recovery paths.
- AI outputs are structured, versioned and validated; models are not the source of truth.
- All data access and actions enforce current authorization and scoped consent.
- Audit records contain correlation and outcome metadata but no credentials, raw documents or unnecessary personal text.
- UI shows evidence, uncertainty, next step, owner, deadline and action state.
- Synthetic/sandbox activity can never enter live VIVC.
- Project status and feature catalog describe the code that actually exists, not planned work.
- Reproducible test and run commands are supplied with the delivery package.
