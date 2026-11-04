# AwnNORA Turbo Parallel Engineering Model

## Objective

Build the product as one coherent Human Economic Intelligence system while allowing specialist workstreams to advance in parallel. Parallelism is at bounded subsystem contracts—not independent feature stubs that later need to be stitched together.

## Workstreams and ownership boundaries

| Workstream | Owns | Must expose | Integration gate |
|---|---|---|---|
| A — Personal Mode & Financial Truth | First-user journey, personal profile, owner-scoped financial facts, cashflow and Power Report | typed read models, domain findings, evidence references | posted-only ledger semantics; owner-scope tests; exact currency math |
| B — Guardian Trust & Defence | evidence intake, quarantine, malware scan, extraction, invoice review, dispute packet | evidence lifecycle and extraction contracts | unscanned/rejected documents cannot reach parsers/review; evidence spans verified |
| C — Entitlements & Opportunity | skills/capabilities, demand, scheme catalogues, eligibility evidence, opportunity proposals | source-versioned match and evidence records | authoritative sources, freshness, missing-evidence handling; no false award |
| D — Crisis Shield | shocks, essential prioritization, safe replanning, relief pathways | crisis case plan and constrained actions | never reflexively push new debt; essential needs and consent gates |
| E — One-Person Enterprise & Resource Exchange | unit economics, catalogue, orders, available capacity and service matching | quotes/listings/commitment state | costs are complete, both parties confirm, cancellation and fulfilment semantics |
| F — Commons | demand signals, cohort aggregation, partner offer comparison and value allocation | privacy-reviewed aggregate and candidate offer contracts | event-time consent, anti-differencing, fairness, positive net benefit, no raw personal records |
| G — GENIEA Runtime | durable missions, typed tools, leases, checkpoints, retries, cancellation, reconciliation | mission/step state machine and tool registry | revoked permission blocks execution; side effects are idempotent or reconciled |
| H — KRN | private evidence/knowledge graph, provenance, temporal facts, retrieval, shared edges | typed facts, provenance spans, graph query contract | private/public partition tests; stale-source and hash mismatch handling |
| I — MAKOS Experience | user cockpit, onboarding, case/workflow UI, approvals, operator console | API-backed screens and event subscriptions | every state visible; human approvals are explicit; synthetic/sandbox/live labels |
| J — Synthetic Scenario & Evaluation | personas, documents, events, failure injection, load fixtures and scorecards | reproducible scenario catalog, data manifest, evaluator | no synthetic data leaks into real metrics; deterministic seed; independent validation |
| K — Platform/SRE/Security | migrations, deployment, observability, rate limits, keys, retention, backups, CI | runtime envelope and operational SLO dashboards | restore/recovery drills, PostgreSQL integration, threat-model gates |

## Parallel execution rules

1. Every workstream gets a bounded branch and a named contract owner. A workstream may not silently redefine another workstream's domain terms.
2. Domain interfaces and state machines are agreed before API/UI implementations diverge.
3. No shared-file conflict is resolved by last-write-wins. Integrate sequentially through the user-controlled branch and inspect each diff.
4. Keep the domain pure; database, HTTP, model, file-store and provider adapters remain at the edges.
5. Every event carries actor, tenant/owner scope, timestamp, environment, idempotency key and provenance where applicable.
6. Models return typed proposals. Deterministic services validate, authorize and commit truth.
7. Every external mutation follows: plan → policy check → current consent/permission check → human approval → idempotent dispatch → provider reconciliation → evidence-backed outcome.
8. When an external provider times out after a possible side effect, reconcile before retry. Never assume exactly-once execution.
9. Feature teams build against synthetic fixtures early, but fixture records are never eligible for real VIVC or external provider calls.
10. Do not put a feature in the user journey until it has an end-to-end acceptance test and honest state labels.

## Integration cadence

- **Contract pass:** glossary, input/output schemas, state machine, errors, trust boundary and event audit.
- **Vertical slice pass:** one user story runs from UI/API through domain and persistence to an observable outcome.
- **Chaos pass:** missing dependencies, invalid data, revoked consent, duplicate requests, concurrency, worker crash, timeouts, provider uncertainty and recovery.
- **Product pass:** first-user usability, accessibility, human approval, clear next action and user-visible value distinction.
- **Release pass:** migrations, rollback, deployment, logs/metrics/traces, security review, backup/restore and real integration proof.

## Current critical path

1. Personal Mode (first session) and real data import/reconciliation.
2. Guardian quarantine/scanning and verified extraction provenance.
3. MAKOS user cockpit that presents findings and approval boundaries.
4. GENIEA durable mission runtime; then connect specialist capabilities through typed tools.
5. KRN evidence/provenance and temporal retrieval.
6. Benefits/opportunity, crisis and one-person enterprise verticals.
7. Commons with privacy/anti-inference controls and verified supplier/settlement pathways.
8. Live integrations only when legal authority, contracts, credentials, sandbox proof and reconciliation exist.

## Definition of Done

A subsystem is done only when its core user journey, domain invariants, migrations, API/UI contract, access controls, audit/provenance, failure recovery, test coverage, evaluation data, observability, operational runbook and honest product-status entry are all delivered. A passing unit test or a successful mock call alone is not completion.
