# AwnNORA Turbo Parallel Engineering Programme

**Execution principle:** parallelize bounded workstreams, not incompatible mini-products. Every workstream shares the same domain contracts, identity, tenancy, consent, provenance, money, environment, audit and event semantics.

**Current execution base:** remote `main` at `a55cb388ef7baf72766e2fcabe89f0dee1c45979`. The Iteration 03 economic-intelligence kernel and context-map reconciliation are implemented locally and tested; remote branch creation remains blocked by GitHub App installation mismatch.

## Workstream map and current state

| Workstream | Owner architecture role | Deliverable | Current state / gate |
|---|---|---|---|
| A. Platform security | Core platform / MAKOS | Owner isolation, consent enforcement, document storage port, rate limits, retention/export/delete, audit and health | Iterations 01–02 establish identity, scoped consent and audit; encrypted document lifecycle and hardening remain open |
| B. Financial intelligence | Data + logic planes | Cashflow coverage, budgets/goals, EMI/loan models, deterministic forecast/scenarios | Accounts, transactions, obligations and posted cashflow are merged; forecast and budget engine not started |
| C. Guardian/document intelligence | GENIEA + MAKOS | Document intake, hash/provenance, extraction, evidence spans, invoice review, case state and draft actions | **Started:** Iteration 03 invoice/evidence domain evaluator and 8 focused checks; document API/vault/OCR/Meta extraction/case persistence still open |
| D. Opportunity/Benefits | GENIEA + KRN | Capability graph, source-versioned rules, eligibility, proof completeness and opportunity ranking | Design only; wait for typed KRN/profile and authoritative source registry contracts |
| E. Enterprise/resource exchange | MAKOS + KRN | Listing/catalog, capacity windows, quote/order/fulfilment, cancellation/refund and unit economics | Design only; provider/commerce adapters and trust/settlement contracts needed |
| F. Commons | GENIEA + KRN | Consented demand signals, cohort suppression, anti-inference, offer lifecycle and net-value optimizer | **Started:** Iteration 03 in-memory consent-aware aggregate and offer optimizer; no persistent Commons service, provider bidding or full privacy analysis |
| G. Durable agent runtime | GENIEA | Persisted mission/step/checkpoint, typed tool registry, retries, idempotency, approvals and resume | **Started at policy layer:** bounded mission state graph and tool approval/environment gate; storage/outbox/checkpoints/runtime still open |
| H. Product surface | MAKOS | Personal Mode onboarding, Personal Power report, evidence/action timeline, Commons story and synthetic/live banner | Context map updated; user-facing MAKOS application not implemented in repo |
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
3. Complete Guardian as the first user-visible vertical slice: authenticated intake -> safe storage/hash -> evidence extraction -> deterministic review -> persisted case -> approval -> audit.
4. Build persistent GENIEA mission runtime with checkpoint/resume for that Guardian workflow.
5. Connect Meta Model API behind a provider-neutral gateway; benchmark evidence extraction and abstention on the synthetic invoice corpus.
6. Build Personal Power report and source-grounded Benefits/Opportunity signals.
7. Persist Commons signals, run anti-inference/privacy analysis and expose transparent offer comparison.
8. Add Enterprise/Resource Exchange and real providers only when partner terms and credentials exist.
9. Deliver MAKOS UX, end-to-end observability and demo instrumentation.

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
