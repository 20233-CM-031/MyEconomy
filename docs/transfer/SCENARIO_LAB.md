# AwnNORA Scenario Lab v1

## Why it exists

The existing `demo_data/synthetic_v1/` corpus is a broad relational snapshot (42 tables, 17,425 rows, 120 fictional customers, 11,538 transactions and multimodal samples). The Scenario Lab complements it with explicit product stories and failure/recovery runs for the full product vision.

## Included default workload

- 46 scenario templates.
- 12 capability categories: Personal, Guardian, Entitlement, Opportunity, Resource Exchange, Crisis, One-Person Enterprise, Commons, GENIEA, KRN, VIVC and Operations.
- 25 deterministic replicas per template by default: 1,150 runs.
- JSONL execution-shaped records, a scenario catalog and SHA-256 manifest.
- Integer INR paise for generated monetary values.
- No emails, phone numbers, real account identifiers, passwords, addresses, provider endpoints or personal data.
- Every run is synthetic; every external side-effect flag is false; every run is excluded from real VIVC.

## Generate more

From repository root:

```bash
python tools/awnnora_scenario_lab/generate.py --out demo_data/scenario_lab_v1 --replicas 25 --seed 20261104
python tools/awnnora_scenario_lab/validate.py demo_data/scenario_lab_v1
```

For a larger local stress corpus, try `--replicas 1000` (46,000 scenario runs). Keep the resulting artifacts out of production databases and production analytics.

## Negative and edge cases

The catalog includes: unclassified income, essential-cost deficit, duplicate transaction, invoice price jump, arithmetic mismatch, low extraction confidence, document prompt injection, MIME/signature mismatch, possible benefit with missing evidence, stale entitlement source, capability lacking portfolio evidence, unsafe/low-quality opportunity, expiring resource, delayed salary, medical shock, multiple EMI pressure, disputed disconnection notice, unprofitable business pricing, Commons below quorum, revoked consent, differencing attack, negative-net offer, late mission failure, unknown provider side effect after timeout, revoked approval, duplicate step delivery, stale KRN source, hash mismatch, private edge requested by Commons, synthetic/estimated value, provider acknowledgement without settlement, duplicate settlement event, cross-tenant access attempt, partner outage and export/erasure request.

## Validator guarantees

The validator checks generated-run uniqueness, synthetic labels, no external side effects, no synthetic VIVC, paise integer semantics, no sensitive identifier keys, Commons consent/privacy/quorum handling, negative-net offer rejection, no false entitlement award, no reflexive new-debt recommendation, agent idempotency/human gates and selected scenario-specific invariants.

This is an invariant checker for the generated fixture corpus, not proof that every application engine already executes these workflows. Each template becomes an application acceptance test only when wired to the relevant live domain service and end-to-end route/UI.
