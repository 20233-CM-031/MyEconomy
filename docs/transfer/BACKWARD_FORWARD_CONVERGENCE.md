# AwnNORA — Backward + Forward Engineering Convergence

**Transfer baseline:** `main` at `7408269421f4c1a166e58ec0310fc9c9da2c2ede` (PR #5 merged)

## 1. The rule: build from the user and from the expected truth

AwnNORA is not complete when a screen exists, a model answers, or a dataset validates in isolation. Every capability must converge across four independently verifiable surfaces:

1. **User contract:** what a person is trying to protect, earn, receive, exchange or operate.
2. **Economic contract:** exact money, eligibility, quality, time, constraints, privacy and expected outcome.
3. **Execution contract:** persisted state, typed API, evidence, consent, audit, idempotency, retry and recovery.
4. **Experience contract:** what MAKOS displays, what the person can approve, and which result can be independently confirmed.

Forward path:

`Person → MAKOS task → Personal Economic Case → GENIEA mission → typed service → deterministic rule → persisted state/evidence → external acknowledgement → settlement → verified VIVC`

Backward path:

`Scenario/outcome → invariant → domain rule → service contract → database/audit model → API → UI acceptance test → observed result`

These two paths meet at a shared typed contract, not at a presentation or mock response.

## 2. Shared object model

The system is moving toward one common **Personal Economic Case**. It is the unit of work shared by Guardian, Opportunity, Entitlement, Crisis, Resource Exchange and Enterprise. The initial v1 contract should contain:

- `case_id`, `owner_user_id`, scope and environment (`SYNTHETIC`, `SANDBOX`, `LIVE`)
- capability, goal, user constraints, priority and due date
- facts with source and effective time
- evidence references with source digest, locator/span, provenance, extraction version and confidence
- current unknowns, stale sources, contradictions and abstention reasons
- options with currency, gross amount, direct costs, fees, effort and net value
- consent references and the exact purpose/category/recipient required
- next action, action payload digest, approval, actor and approval expiry
- attempt, provider acknowledgement, settlement, verification and compensation state
- append-only timeline and a VIVC attribution record

This is a target shared contract, not yet a persisted ORM model in the repository. Start with one vertical slice before generalizing all cases.

## 3. Backward acceptance from the Scenario Lab

The existing 46-template / 1,150-run Scenario Lab supplies negative and positive product situations. It does **not** prove that each engine runs. Convert each template into a six-part acceptance family:

| Test layer | Expected purpose |
|---|---|
| Happy path | A supported case reaches the correct deterministic decision |
| Boundary | Expiry, date, currency precision, minimum amount, cohort size or confidence threshold |
| Invalid / adversarial | Spoofed file type, malformed input, prompt injection, impossible arithmetic, unsafe terms |
| Authorization | Cross-owner access, wrong recipient, missing or revoked consent |
| Dependency failure | Database outage, model timeout, scanner unavailable, provider timeout |
| Retry / recovery | Replayed import, worker restart, duplicate webhook, unknown side-effect state, cancellation |

A fixture becomes an application acceptance test only when the scenario invokes the real service/API, checks the persisted state and checks the UI-visible result. A validator that checks JSON structure is a dataset validator, not an engine test.

## 4. Forward implementation by real user journey

### Journey A — first person receives useful analysis

Current merged runtime:

- register / verify / sign in;
- create financial account;
- bounded CSV import with idempotency and provenance;
- owner-private posted cashflow;
- Personal Power Report with essential obligations and potential duplicate warnings.

This transfer adds the MAKOS client path for account creation, CSV import and report refresh. A report is still not a verified saving. The next increment should allow a finding to be opened into a persisted Personal Economic Case, attach evidence and select a safe next action.

### Journey B — user disputes a bill safely

Current runtime: private upload, SHA-256, invoice review using caller-supplied structured fields, deterministic finding, persisted case and manual draft/approval state. Documents remain `STORED_UNSCANNED`.

Required convergence:

`upload → quarantine → scanner → CLEAN → parser sandbox → multimodal extraction → field/source-span validation → deterministic invoice rules → case timeline → user edits/approves → export packet or authorized provider action → acknowledgement → settlement/recovery verification`

No PDF/image content may be sent to a model before a real malware scanner and isolated parser exist. Low confidence or invalid locator/hash means abstention. Human approval is tied to the exact action payload hash.

### Journey C — skill becomes income

Required convergence:

`skill and proof → available hours/tools → demand source and freshness → constraints/quality/safety → gross price → travel/material/time/platform cost → net earning → user opts in → proposal → delivery evidence → payment reconciliation → verified earnings`

Do not rank opportunities by headline pay or expose a user's private profile to a client before explicit approval.

### Journey D — benefit is actually obtained

Required convergence:

`official source/version → jurisdiction and effective dates → deterministic eligibility constraints → missing proof/deadline → user-reviewed application pack → authorized submission → authority acknowledgement → award/credit confirmation → verified benefit event`

A fixture match, possible eligibility, or submitted application is not an award.

### Journey E — Commons creates collective purchasing leverage

Required convergence:

`individual need → separate purpose-specific consent → minimized signal → event-time authorization → privacy/query controls → cohort and offer constraints → net-value calculation → supplier validation → clear terms → each user confirms → fulfilment/cancellation → settlement → transparent distribution`

Raw bank statements, identifiable hardship, documents and person-level transaction records stay inside the private boundary. A cohort threshold alone is not differential privacy.

## 5. Parallel engineering ownership

| Parallel lane | Primary ownership | Independent delivery | Must not modify without integration approval |
|---|---|---|---|
| MAKOS Web | `apps/web/**` | onboarding, import/report, cases, approvals, accessible responsive design | money/consent/mission rules |
| Guardian trust | Guardian routes, application, migration, scanner/storage adapter, tests | quarantine, scanning, extraction provenance and invoice case | shared consent/model contracts |
| GENIEA runtime | mission persistence, job/outbox worker, retry and lease tests | durable read-only mission and approval gate | external tool policy and shared state contracts |
| KRN evidence | provenance/evidence/temporal store and retrieval tests | private fact/evidence links and source freshness | visibility/consent boundary |
| Economic engines | opportunity/entitlement/crisis/resource/enterprise services | one end-to-end economic outcome at a time | money, identity and VIVC kernel |
| Meta model lab | gateway adapters, model prompts/schemas, eval corpus | measurable extraction/explanation/voice/visual task | deterministic truth and external side effects |
| Scenario QA | scenario-to-service harness, load/recovery/privacy eval | API/UI acceptance, chaos and regression matrix | never edits product rules to fit fixture outputs |
| Integrator | shared contracts, code review and release record | integrated, tested package and feature truth | sole editor of shared migration/version/status changes |

Parallel work starts only after a contract card exists: goal, typed input/output, states, errors, data category, consent purpose, environment, audit event, idempotency key, timeouts, tests and file ownership.

## 6. Meta model placement across the system

| Meta model | AwnNORA-specific job | Current state in this transfer | Required evaluation |
|---|---|---|---|
| Muse Spark 1.3 Standard | Explain deterministic reports now; later interpret CLEAN documents, extract proposed fields and create bounded mission plans | One aggregate-only report explanation endpoint is implemented. No document extraction or GENIEA tool execution. | schema pass rate, finding ID validity, abstention, explanation usefulness, hallucination rate, latency, tokens and cost |
| Muse Wonder 1.0 Standard | Longer, multi-step GENIEA mission planning/delegation for complex household or enterprise tasks | Target only; no API adapter or durable mission runtime | task completion, checkpoint recovery, delegation precision, tool-call safety and total mission cost |
| Muse Voice Transcribe 1.0 | Voice-first household intake, clarification and case notes | Target only; no microphone/WebSocket client or transcript persistence | transcript correction rate, turn attribution, supported-language coverage and consent flow |
| SAM 3.1 | Visual inventory/resource understanding: detect objects, count/segment equipment, crates, tools or product stock | Target only; no segmentation adapter or object verification | mask/box quality, counting accuracy, tracking identity, human correction and false matches |
| Muse Glimmer | Local open-weight model for offline or privacy-sensitive explanation and evaluation | Target only; no packaged weights/runtime | task quality vs Spark, hardware/VRAM, throughput, thermal/power profile, privacy boundary and abstention |
| Muse Spark Open | Higher-capability open-weight research/agentic track if hardware or hosted provider supports it | Target only; no weights or runtime shipped | realistic serving cost, memory/throughput, task quality, safe tool integration |
| Muse Image 1.0 | Optional one-person enterprise catalogue/product artwork from user-approved assets | Target only; not part of critical path | brand consistency, product fidelity and human approval |

Use each model because it contributes a distinct system capability. Never use SAM as an OCR model or identity verifier. Muse Voice returns transcript text, not speech synthesis. Muse Spark's current audio input support has documented limitations; use the dedicated Voice Transcribe path for audio transcription.

## 7. Integration gates

No workstream is considered integrated until all are true:

1. Same schema and domain invariants across API, worker and UI.
2. Owner/tenant scope and purpose-specific consent verified at the protected read/action.
3. Money and outcome math handled by deterministic code with explicit currency.
4. Environment adapter enforced (`SYNTHETIC`, `SANDBOX`, `LIVE`).
5. Idempotency, retry, timeout and uncertain-side-effect behavior tested.
6. Append-only audit contains correlation and outcome state without secrets/raw prompts/documents.
7. User sees source, uncertainty, next step, owner, deadline and approval state.
8. Synthetic outcomes cannot count as real VIVC.
9. Scenario tests execute actual services and validate persisted DB state.
10. SQLite and PostgreSQL migration/integration tests, lint, typecheck, build and accessibility checks pass.

## 8. Delivery cadence

Build narrow, testable vertical slices in parallel; merge them locally in a single integration branch/check-out after contract review. Never accumulate disconnected stubs. At each integration checkpoint, deliver:

- source files plus path manifest;
- migration/rollback notes;
- positive, negative, boundary, isolation, retry and recovery tests;
- exact commands and observed outputs;
- demo script and synthetic input;
- current capability status (implemented, partial, simulation, target);
- performance/model quality and cost evidence;
- outstanding production gates.

**Current state:** PR #5 is the merged baseline. This package adds the MAKOS Web slice and consent-gated Muse Spark explanation. Guardian trust/scanning, durable GENIEA, KRN, all other economic engines and real provider integrations remain subsequent engineering slices.
