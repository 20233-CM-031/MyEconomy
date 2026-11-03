# Iteration Plan

## Iteration 00 — Engineering Foundation + Cashflow Analysis Slice
**Status in this delivery:** Implemented locally; 11 automated tests pass and local HTTP smoke tests pass. Not yet pushed to GitHub because the connected GitHub integration rejected repository writes (403).

Scope:
- Repository structure, package metadata and engineering documentation.
- Modular monolith boundary and domain/application/API separation.
- Health/readiness endpoints.
- Deterministic period cashflow calculation.
- Currency precision validation for the supported currency registry.
- API contracts and automated tests.

Acceptance criteria:
- Application imports and starts.
- Health and readiness return expected status.
- Cashflow endpoint calculates income, expense, net, essential/discretionary totals, category order and rate correctly.
- Amounts use Decimal, not float.
- Period mismatch, unsupported currency, extra fields and invalid precision are rejected.
- Unit and API tests pass.

Explicit exclusions:
- No persisted personal data, login, bank integrations, offer provider, claims integration, LLM or external side effects.

## Iteration 01 — Identity, Consent and Personal Data Ownership
- Define threat model, account/session lifecycle, tenant and household ownership.
- Implement authentication, authorization policy and revocable consent ledger.
- Add PostgreSQL, migrations, encrypted secret handling and audited personal data access.
- Implement data export and deletion workflow design.
- Acceptance: cross-user access tests, consent revoke tests, migration rollback test, audit verification.

## Iteration 02 — Financial Data Foundation
- Design normalized account, transaction, recurring obligation, liability and budget models.
- Add import pipeline with idempotency, deduplication, provenance and reconciliation.
- Add deterministic cashflow forecasts and scenario analysis.
- Integrate bank/account aggregation only where a licensed/authorized provider and credentials are available; manual/CSV import is a real fallback.
- Acceptance: duplicate import tests, reconciliation invariants, currency correctness, concurrent updates and end-to-end import tests.

## Iteration 03 — Day-One Personal Power Discovery
- Intake wizard with user-controlled fields and data upload.
- Personal Power Report with sourced insights, uncertainty and evidence.
- At least one actionable flow completed end-to-end using a real public/partner source.
- Measure user action and outcome; distinguish estimated from verified value.

## Iteration 04 — Guardian and Economic Defence
- Case lifecycle, evidence store, anomaly/risk rules, complaint drafting and follow-up.
- Real complaint/provider integrations only when verified and authorized; otherwise export-ready user-controlled artifacts.
- Threat model against phishing, prompt injection and unsafe external actions.

## Iteration 05 — Benefits and Opportunity Graph
- Structured authoritative scheme catalogue, rules/provenance, eligibility explanation.
- Skills, capability, availability and opportunity matching.
- Application/task workflow and outcome verification.

## Iteration 06 — Personal Enterprise Engine
- Demand research, product/service catalogue, pricing and unit economics.
- Orders, enquiries, invoices and profitability workflows.
- External commerce/payment integrations only after provider credentials and compliance.

## Iteration 07 — Resource Exchange
- Verified resource and need listings, matching constraints, availability, location and trust signals.
- Booking/commitment lifecycle, cancellation and dispute process.

## Iteration 08 — Collective Economic Intelligence / Commons
- Explicit group-purpose consent and privacy-preserving aggregate demand.
- Minimum cohort thresholds and anti-inference protections.
- Provider offers, offer verification, net-benefit optimizer, group commitment and cancellation safety.
- User approval and transparent sharing/revenue ledger.

## Iteration 09 — Agent Runtime and Durable Missions
- Typed tool registry, policy enforcement, mission state machine, checkpoint/resume, retry budgets and idempotency.
- Long-running workflows with visible trace, evidence, approvals and human escalation.
- Model provider abstraction and Meta model integration where relevant to hackathon rules.

## Iteration 10 — Crisis Shield + Integrated Demo
- Replanning under income or expense shocks.
- End-to-end scenario across personal protection, opportunities, resource matching and Commons.
- Clearly separate live integrations, verified outcomes, estimates and simulated future network elements.

## Definition of Done for every iteration
1. Written user story, threat surface and explicit non-goals.
2. Domain invariants and API/data contracts reviewed.
3. Unit, integration and negative-path tests.
4. Authorization, privacy, idempotency and concurrency behavior tested where applicable.
5. Observability for success, failure, retries and external dependencies.
6. Runtime validation against a reproducible environment.
7. Documentation, migration and rollback plan.
8. Acceptance criteria demonstrated before moving on.
