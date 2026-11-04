# AwnNORA Meta Model Evaluation Plan

The product must demonstrate a system-level use of Meta AI, not a cosmetic model call. Each model has a named job, a controlled input boundary, an output contract and a task-specific benchmark.

## Current implementation: Muse Spark explanation

- Model ID: `muse-spark-1.3` (Standard mode).
- Endpoint: `POST https://api.meta.ai/v1/chat/completions`.
- Input: aggregate Personal Power totals, period metadata and up to 12 deterministic finding descriptions/IDs. No person, account, transaction, payee, contact, document or evidence-span identifiers.
- Consent: separate `ai_assistance` grant for `financial_summary` and `household_obligations`, recipient `meta-model-api`; both required.
- User input: a fixed four-value intent enum. No arbitrary prompt field is accepted from the browser.
- Output: strict JSON Schema, maximum four suggested explanations/actions, every `finding_id` must be one of the allowed deterministic IDs.
- No tools, `store=false`, no external mutations and no model-computed money, awards, settlements or verified impact.

## Evaluation set for this endpoint

Use a fixed held-out dataset derived from synthetic report fixtures with manually authored expected intent and permissible finding IDs. Separate it from prompt-development examples.

| Metric | Definition | Initial release gate |
|---|---|---|
| Schema validity | responses matching the strict response contract | 100% |
| Finding reference validity | every action refers to a finding from the supplied report | 100% |
| Monetary fact integrity | no model-created or altered monetary values appear in output | 100% |
| Unsupported outcome claims | model claims recovery, payment, award, fraud or settlement without evidence | 0 |
| Personal-data leakage | forbidden direct/transaction-level fields appear in outbound request logs/test capture | 0 |
| Useful explanation | blinded human rating for clarity, accuracy and useful next step | report distribution, not a fabricated threshold |
| Abstention correctness | model states when data is incomplete, stale or insufficient | measured by scenario family |
| Latency and cost | median/p95 end-to-end latency and token/currency cost | record actual, tune after baseline |

The 100% gates are safety constraints, not expected model-quality metrics. If a response violates a gate, the system rejects it and shows an unavailable/needs-review state.

## Guardian model evaluation, after quarantine/scanning exists

Only `CLEAN` files may enter a sandboxed parser/OCR path. Then use Muse Spark multimodal input to propose structured invoice fields with page and region references. Persist model ID, prompt version, schema version, source SHA-256, page, bounding region, extracted value, confidence and warnings.

Evaluate against the 12 existing multimodal invoice examples and expanded hard negatives:

- field exact-match for invoice ID, dates, quantities, unit price, line total, subtotal, taxes, fees, credits and total;
- evidence-span / region precision and recall, verified against the exact source digest;
- arithmetic reconciliation in deterministic code;
- confidence calibration and abstention under blur, rotation, low resolution, missing page and conflicting fields;
- prompt-injection handling, where document instructions are treated only as untrusted content;
- malicious/malformed file handling and scanner/parser failure isolation.

Do not tune the rule kernel to reproduce a model's wrong output. The model proposes facts; deterministic services validate them.

## Voice and physical-resource evaluation

Muse Voice Transcribe should turn a spoken request into a transcript and editable structured intake. Test English, Hindi, Telugu and code-switching only where supported by the current Voice model docs and actual test access. Capture speaker labels/turns as provenance. The user confirms extracted names, amounts, locations and deadlines before persistence.

SAM 3.1 should support a specific physical-resource workflow: segment visible tools/equipment or produce crates from images/video, return boxes/masks, then let a human confirm count, condition and availability. Segmentation is not proof of ownership, identity, safety or actual capacity.

## Local model / open-weight evaluation

Muse Glimmer is the primary local evaluation candidate for private/offline tasks. Keep the same task set, input schema and output validator as the hosted path. Compare answer quality, extraction exact-match, abstention, prompt-injection resilience, runtime memory, throughput, latency, energy and operating cost. The model stays local; the inference endpoint must not be exposed to the public web without authentication and network controls.

Muse Spark Open is a separate larger open-weight track. Do not assume it is practical to self-host on a single consumer GPU. Check actual weight variant, hardware, serving runtime and license before committing.

## Evidence required in the hackathon submission

Capture actual request/response IDs where available, model IDs/modes, schema pass rates, benchmark outcomes, latency/cost, input minimization, consent/revocation behavior, failure cases and a real screen recording. Label any model/API call that was not actually executed as planned, not implemented.
