# Iteration Plan

This plan preserves the complete personal-first / Commons end vision while shipping bounded vertical slices. The full roadmap is not a promise that every capability will be live for the hackathon; the live demo must label implemented, simulated and planned elements.

## Iteration 00 — Engineering Foundation + Cashflow Analysis Slice
**Status:** Implemented locally; see `docs/iterations/ITERATION-00.md`.

Scope delivered: Python package, modular monolith boundaries, FastAPI/Pydantic API, health/readiness, exact Decimal cashflow analysis, currency minor-unit validation, tests, CI/container and engineering memory.

## Iteration 01 — Identity, Email Verification, Household and Consent Trust Foundation
**Status:** Core slice implemented and locally tested; production hardening remains open. See `docs/iterations/ITERATION-01.md` and `docs/THREAT_MODEL.md`.

Scope delivered:
- SQLAlchemy/Alembic schema for users, sessions, email challenges, household membership/invitations, consent grants and audit events.
- Argon2 password hashes, digest-only opaque tokens, session expiry/revocation.
- Single-use email challenge and development/SMTP delivery adapter.
- Verified-account gating for household/consent operations.
- Household invite and acceptance, separate from per-user consent.
- Purpose/category/recipient/version/expiry consent and revocation.
- Append-only audit records and DB readiness checks.

Known gaps: no real SMTP provider tested, invitation delivery remains manual, no live PostgreSQL test, no account recovery/MFA or distributed rate limiting, and no data-reader enforcement path because financial data is not yet persisted.

## Iteration 02 — Financial Data Foundation
- Design normalized accounts, statements/import batches, transactions, recurring obligations, liabilities, budgets and currency/provenance records.
- Implement import pipeline with idempotency keys, deterministic duplicate detection, correction/reversal semantics, import provenance and reconciliation.
- Support manual/CSV import first; bank aggregation only where an authorized/contracted provider and credentials exist.
- Integrate data-access authorization and exact-scope consent enforcement in the same transaction for all personal/household data reads and exports.
- Add temporal data semantics and deterministic cashflow projections/scenarios.
- Acceptance: duplicate and replay tests, reconciliation invariants, currency correctness, transaction rollback, concurrent import behavior, cross-tenant denial and end-to-end import tests.

## Iteration 03 — Day-One Personal Power Discovery
- User-controlled onboarding and minimal profile/intake.
- Personal Power Report from authoritative public sources plus authorized data.
- At least one actionable workflow completes for a single user without Commons/network dependency.
- Show provenance, uncertainty, potential vs verified value, and a user-controlled next action.
- Meta model integration only where a task needs it; compare against deterministic/baseline approach.

## Iteration 04 — Guardian and Economic Defence
- Case lifecycle, evidence/document ingestion, billing/contract checks, anomaly/risk rules, complaint drafting and follow-up.
- External action requires a supported integration and explicit approval; otherwise generate an export-ready package.
- Protect against phishing, malicious documents, prompt injection and unsafe side effects.

## Iteration 05 — Benefits, Opportunity and Capability Graph
- Authoritative benefit catalogue with source/version/eligibility rule evidence.
- Skills, capability, availability and opportunity matching.
- Application/action workflows and outcome confirmation; possible eligibility is never called an award.

## Iteration 06 — Personal Enterprise Engine
- Demand research, unit economics, catalogues, pricing, storefront and enquiry/order/invoice/profit workflows.
- Commerce, messaging and payment integrations only with credentials and compliance.

## Iteration 07 — Resource Exchange and Crisis Shield
- Verified need/resource listings, capacity, availability, location, matching and commitments.
- Cancellation, refunds, disputes and safe crisis re-planning.
- Do not default to loan recommendations for a person in financial distress.

## Iteration 08 — Collective Economic Intelligence / Commons
- Purpose-specific opt-in aggregation; strict separation between membership and consent.
- Minimum cohort sizes, suppression, inference attacks, differencing and re-identification controls.
- Match aggregated demand with verified capacity, offers, resources and funding.
- Provider terms, net-value optimization, group commitment/cancellation and transparent economics.
- Human approval for consequential commitments; no raw private transactions sent to Commons by default.

## Iteration 09 — Agent Runtime, Meta Models and Durable Missions
- Provider abstraction with model-tier/data-policy gate.
- Typed tool registry, capability scopes, durable mission state, checkpoints, idempotency keys, retry budgets, timeouts, audit and resumption.
- Model output is schema-constrained and checked by deterministic code.
- Benchmark Muse Glimmer locally for private agent tasks; evaluate Muse Spark/Wonder Standard API for complex multimodal/agentic tasks. No personal/confidential information may be sent to Contributor Services.
- Acceptance: interrupted multi-step task resumes without duplicate side effects; malformed model output/failure/revoked consent blocks execution.

## Iteration 10 — Integrated Demo and Measurement
- Coherent one-to-three synthetic-user narrative spanning Personal Mode, Guardian, Opportunity/Benefits, Commons and agent checkpoints.
- VIVC ledger separating estimated, attempted, pending and verified outcomes.
- Model/tool traces, performance/cost/quality baselines and meaningful Meta tooling evidence.
- Clear final-vision diagram; all unavailable integrations and synthetic partner bids labelled.
- Map every demo segment to the scoring rubric in `docs/HACKATHON_SCORECARD.md`.

## Definition of Done for every iteration
1. User story, impact hypothesis, threat surface, explicit scope and non-goals.
2. Domain invariants, API/schema, database and authorization design before code.
3. Unit, integration, negative-path, boundary, concurrency and retry tests as applicable.
4. Real runtime validation with reproducible commands; external integration tested against sandbox/live endpoint when credentials exist.
5. Observability, audit, privacy, data retention and failure/compensation behavior documented.
6. Migration, rollback, idempotency and deployment sequence documented.
7. Codebase map, feature catalog, project memory, status and iteration record updated.
8. Acceptance criteria demonstrated before next iteration starts.

## Iteration 07 — Personal Casebook

Turn Personal Power findings into owner-private, idempotent, versioned workflow cases with immutable event history and a MAKOS case workspace. This is a workflow spine, not external execution or outcome settlement.
