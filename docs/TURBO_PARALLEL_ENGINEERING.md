# AwnNORA Turbo Parallel Engineering Programme

**Execution principle:** parallelize bounded workstreams, not incompatible mini-products. Every workstream shares the same domain contracts, identity, tenancy, consent, provenance, money, environment, audit and event semantics.

**Current verified remote base:** `main` at `5b5cf669773d5c0cd33f5abffb8c46d44cead797` (PR #3 merged). Iteration 03 domain kernel is merged. Iteration 04 Guardian API vertical is implemented in a local candidate worktree; 84 tests pass, but the candidate is not pushed because GitHub branch creation still returns 403.

## Workstream map and current state

| Workstream | Owner architecture role | Deliverable | Current state / gate |
|---|---|---|---|
| A. Platform security | Core platform / MAKOS | Owner isolation, consent enforcement, document storage port, rate limits, retention/export/delete, audit and health | Iterations 01–02 establish identity, scoped consent and audit; encrypted document lifecycle and hardening remain open |
| B. Financial intelligence | Data + logic planes | Cashflow coverage, budgets/goals, EMI/loan models, deterministic forecast/scenarios | Accounts, transactions, obligations and posted cashflow are merged; forecast and budget engine not started |
| C. Guardian/document intelligence | GENIEA + MAKOS | Document intake, hash/provenance, extraction, evidence spans, invoice review, case state and draft actions | **Started / local vertical slice:** Iteration 04 adds authenticated evidence intake, local private blob adapter, persisted invoice cases, owner-scoped review APIs, draft and approval state; storage scanning/OCR/Meta extraction/source-span verification and provider delivery are still open |
| D. Opportunity/Benefits | GENIEA + KRN | Capability graph, source-versioned rules, eligibility, proof completeness and opportunity ranking | Design only; wait for typed KRN/profile and authoritative source registry contracts |
| E. Enterprise/resource exchange | MAKOS + KRN | Listing/catalog, capacity windows, quote/order/fulfilment, cancellation/refund and unit economics | Design only; provider/commerce adapters and trust/settlement contracts needed |
| F. Commons | GENIEA + KRN | Consented demand signals, cohort suppression, anti-inference, offer lifecycle and net-value optimizer | **Domain kernel merged:** in-memory consent-aware aggregate and offer optimizer; persistent Commons, anti-differencing/privacy analysis, provider bidding and settlement not started |
| G. Durable agent runtime | GENIEA | Persisted mission/step/checkpoint, typed tool registry, retries, idempotency, approvals and resume | **Policy kernel merged:** bounded mission state graph and tool approval/environment gate; persisted mission store/outbox/checkpoints/runtime still open |
| H. Product surface | MAKOS | Personal Mode onboarding, Personal Power report, evidence/action timeline, Commons story and synthetic/live banner | API workflow contracts now exist for Guardian; user-facing MAKOS application and Personal Mode/Commons UI are not implemented |
| I. Meta model/evaluation | GENIEA model gateway | Meta model router, multimodal invoice extraction, tool proposal evaluation and local Glimmer benchmark | Not integrated; gateway contract and model credential/access required. Do not place sensitive information into an unsuitable service tier |

## Shared engineering interfaces

- `ModelGateway`: `extract_document`, `classify_document`, `reason_over_evidence`, `propose_plan`, `propose_tool_call`; returns typed output, model ID, input/output usage, latency and warnings.
- `DocumentStore`: immutable object write/read/delete with owner ID, object key, SHA-256, media type, size, storage class and retention metadata.
- `ProviderAdapter`: environment, capabilities, idempotency support, timeouts, result provenance and reconciliation query.
- `ConsentPolicy`: exact purpose + categories + recipient + expiry + revocation check; called within the same transaction as protected access.
- `MissionStore`: atomic state transition, step lease, checkpoint, action record, approval and outbox event.
- `EconomicRules`: deterministic invoice arithmetic, offer net-value, eligibility constraints, quorum, VIVC and revenue split. The first five kernel primitives now exist in `domain/economic_intelligence.py`; application wiring remains next.
- `KRNRepository`: typed nodes/edges, private/shareable visibility, provenance, time validity and consent link.

## Active integration order

1. Keep AwnNORA identity and full MAKOS / GENIEA / KRN responsibilities synchronized in the context map and repository memory. **Local context-map update complete.**
2. Freeze common document/provenance and environment contracts.
3. Harden the Iteration 04 Guardian slice: add malware scanning/quarantine, production encrypted storage, retention and validated source locators; run service-backed PostgreSQL tests.
4. Add a provider-neutral Meta OCR/multimodal extraction gateway, schema/version trace, field-level evidence and benchmark/abstention evaluation on the Guardian synthetic PDFs.
5. Build durable GENIEA missions/steps/checkpoints, leases, outbox, idempotent execution, approval expiry and resume/reconciliation around Guardian.
6. Build MAKOS UI for Personal Mode, Personal Power report, document evidence timeline, review findings, draft preview and approval.
7. Build KRN typed evidence/knowledge/relationship store with private partitions, temporal provenance and explicitly shared edges.
8. Build source-grounded Benefits/Opportunity and a verified VIVC outcome path.
9. Persist Commons signals/offers, enforce consent and anti-inference, add privacy/fairness review and offer comparison.
10. Add Crisis Shield, Economic Defence, Resource Exchange and One-Person Enterprise as integrated vertical slices.
11. Add live banks, providers, funding/payouts only when lawful authority, contract, credentials, idempotency and reconciliation are in place; never substitute demo mocks.

## Parallel work rules

- Parallelize independent deliverables only after schema/API ownership and contracts are agreed.
- Avoid multiple contributors editing the same migration, project status or shared domain types simultaneously. One integration owner reconciles shared documents at the end of each slice.
- Every slice has problem statement, scope, non-goals, typed contracts, failure states, positive/negative/boundary/authorization/retry tests and acceptance evidence.
- Run Python 3.12 and 3.13, Ruff lint/format, full pytest, SQLite migration lifecycle, PostgreSQL 16 service tests and synthetic dataset validators.
- Update `AWNNORA_CONTEXT_MAP.md`, `PROJECT_MEMORY.md`, `PROJECT_STATUS.md`, `CODEBASE_MAP.md`, `FEATURE_CATALOG.md` and the iteration record with each integrated change.
- Never label design, mock, synthetic fixture or domain-only rule as a live end-to-end feature.

## Meta model workflow

Use Meta models where they create measurable value: invoice PDF/image extraction with page/region evidence, source-grounded explanations, constrained planning and structured tool proposals. Never let model-generated arithmetic, permissions, eligibility, settlements, consent or VIVC become authoritative. Evaluate extraction exact-match, evidence-span precision, confidence calibration/abstention, prompt-injection resistance, tool-call accuracy, latency and cost.

Use the appropriate Meta service tier for personal/confidential information. Benchmark a suitable open-weight local model for sensitive local processing. Verify current model availability, geography, data handling and event eligibility against official documentation immediately before integration/submission.


## Iteration 04 integration result (2026-11-04)

The local Guardian vertical currently supports this end-to-end API journey: verified authentication → bounded upload → signature/type/size check → SHA-256 → owner-scoped idempotency → local private blob + metadata → structured invoice submission → deterministic arithmetic/evidence/confidence/prior-bill review → persisted case/findings/audit → draft → explicit approval state. The approval endpoint does not send a message. The document remains `STORED_UNSCANNED`; a PDF's contents are not parsed and no Meta model is called.

Local evidence: `PYTHONPATH=src pytest -q` (84 passed), compileall, SQLite migration lifecycle, dataset validator (42 tables/17,425 rows). Python 3.12, Ruff and live PostgreSQL 16 for the Guardian migration are not verified. The latest GitHub main SHA remains the PR #3 merge; the Iteration 04 branch creation attempt returned 403 and no remote changes were made.


<!-- AWNNORA-TRANSFER-ITERATION-05 -->
## Parallel workstream contract

See `docs/transfer/TURBO_PARALLEL_DELIVERY_MODEL.md` for the updated parallel workstream boundaries, integration gates and definition of done. Parallelize bounded subsystem work against agreed typed contracts. Do not create disconnected stubs, duplicate money/consent logic, leak raw private records into Commons, or allow models to mutate external state. Every workstream must land a complete testable vertical slice and update shared project status only after integration evidence exists.
