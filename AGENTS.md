# Repository Instructions for AI and Human Contributors

This file is the entry point for anyone (including AI coding assistants) working in this repository.

## Before making any change

1. Read `README.md` and this file.
2. Read `docs/PROJECT_MEMORY.md`, `docs/PROJECT_STATUS.md`, `docs/FEATURE_CATALOG.md`, and `docs/CODEBASE_MAP.md`.
3. Read `docs/THREAT_MODEL.md` and `docs/HACKATHON_SCORECARD.md`, then the relevant feature specification, latest iteration record, engineering standard, and ADRs.
4. Inspect the current Git branch, working tree, commit history, and the exact source files to be changed. Never assume a previous chat summary reflects the current repository state.
5. Confirm whether a requested capability is implemented, partially implemented, designed only, simulated, or not yet designed.

## Product and brand constraints

- The product's final brand name is **not selected**. `MyEconomy` is the repository/internal project name only.
- Do not treat AWNORA or any other prior suggestion as approved. The user has not confirmed a final brand.
- Any future name must feel lively, modern, memorable and globally pronounceable. Do not propose Sanskrit-derived or Christian/religiously coded names. Do not presume that Arabic-derived naming is automatically desired; present it only as an optional creative direction if relevant.
- The product vision is broader than budgeting or fintech: individual economic agency, protection, opportunity, enterprise enablement and consent-based collective economic intelligence.

## Engineering rules

- Build complete, testable vertical slices. Do not generate broad, unintegrated feature stubs or claim mock integrations are live.
- Keep the domain independent of web frameworks, databases, model SDKs and provider SDKs.
- Use typed API contracts, explicit domain invariants, migrations, transactional integrity and documented interfaces.
- Never use binary floating-point for money. Carry currency on every amount. Never combine currencies without a sourced, dated FX conversion.
- Deterministic code owns calculations, eligibility rule evaluation, authorization, constraints, state transitions, idempotency and outcome accounting. Models can interpret, retrieve, explain, rank and plan within controlled boundaries.
- No LLM gets unrestricted database, payment, identity or external-action access. Every tool must have a typed contract, permission check, timeout, retry policy and audit trace.
- Personal data is private by default. Sharing is purpose-specific, minimized, revocable and auditable. Commons must not expose raw household records.
- Consequential actions require explicit user approval and enforceable scoped authorization.
- Distinguish estimates, leads, proposed actions, attempted actions, confirmed actions and externally verified outcomes.
- Test normal, boundary, invalid, failure, authorization, concurrency and retry cases as applicable.
- Record observability, provenance, failure behavior, migration/rollback and acceptance evidence.

## Iteration protocol

For every iteration:

1. Write problem statement, user stories, scope, non-goals and acceptance criteria.
2. Inspect related code and prior decisions; document changed assumptions.
3. Design data model, domain invariants, API contracts, trust boundaries and failure modes before implementation.
4. Implement one coherent vertical slice with tests.
5. Run formatting, lint, unit, integration and end-to-end/runtime checks.
6. Update `docs/PROJECT_STATUS.md`, `docs/CODEBASE_MAP.md`, `docs/FEATURE_CATALOG.md`, `docs/PROJECT_MEMORY.md` and the iteration record whenever the change affects them.
7. Produce a file manifest for the user: exact repository path, whether added/modified/deleted, purpose, important dependencies, and exact push instructions.
8. Use a scoped branch and conventional commit. Do not force-push or overwrite unrelated user work.

## Required response to the user after code work

Always explain:
- what has actually been implemented and what remains planned;
- exact tests and runtime checks actually run, including failures;
- every file added/modified/deleted and its repository path;
- the exact Git commands to apply, commit and push the change;
- any external access, credential or integration blocker.

Never claim a file was pushed, a partner was contacted, a payment occurred, or an integration is live unless the remote system confirms it.

## Long-term project context

Use `docs/PROJECT_MEMORY.md` as the high-level durable product and engineering memory. Use `docs/CODEBASE_MAP.md` for line-of-responsibility and runtime flow. Use `docs/FEATURE_CATALOG.md` as the implementation-status ledger. Use `docs/PROJECT_STATUS.md` for the current factual state. These documents must be kept synchronized with actual code.

## Synthetic fixtures and demos

- `demo_data/synthetic_v1/` is fictional demo/test data only. Do not call it a real customer base or measured impact.
- Keep CSV, JSON, JSONL, PostgreSQL seed and SQLite exports synchronized. Re-run the generator/override, SQLite builder and independent validator after fixture changes.
- Preserve `.invalid` emails, invalid phone placeholders, broad locality clusters and no real identity/financial credentials.
- Every UI/API/demo view derived from fixtures must display a synthetic/demo label; no simulated payment, partner quote, benefits award, claim, application or value event may be presented as live.
