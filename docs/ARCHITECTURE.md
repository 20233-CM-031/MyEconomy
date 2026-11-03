# Architecture Overview

## 1. System shape

Start with a **modular monolith** and explicit domain boundaries. Deploying many microservices before there are independent scaling, team ownership or reliability needs creates operational cost without useful autonomy. Modules communicate through application interfaces and domain events; they must not reach directly into one another's persistence internals.

## 2. Initial logical boundaries

| Module | Responsibility | Authority |
|---|---|---|
| Identity & Access | accounts, sessions, authorization, household membership | source of identity and access decisions |
| Personal Context | user goals, preferences, skills, capability profile | private user-owned context |
| Financial Core | accounts, entries, obligations, budgets, deterministic calculations | authoritative numeric calculations |
| Guardian | claims, cases, evidence and follow-up tasks | workflow; never invents legal outcomes |
| Benefits | schemes, eligibility rules, evidence and application status | sourced rule evaluation; official award remains external |
| Opportunity | skills, availability, jobs, projects and outcomes | matching and workflow |
| Resource Exchange | supply, demand, capacity, inventory and logistics | verified listing/match state |
| Commons | consented demand aggregation, offers, group commitments | privacy-gated collective matching |
| Enterprise | small-business planning and operational workflows | user-approved business operations |
| Agent Runtime | planning, scoped tools, human approval and execution traces | cannot bypass domain authorization |
| Value Ledger | evidence-backed realized outcomes and partner revenue split | auditable outcome accounting |

## 3. Request and execution flow

1. An authenticated user sends a command or request.
2. API validates syntax and authentication.
3. Application service authorizes the specific action and loads only required data.
4. Domain logic enforces invariants and deterministic calculations.
5. Persistence transaction writes state and audit evidence.
6. An outbox event is committed with the business transaction.
7. A durable worker processes external side effects idempotently.
8. Agents may interpret evidence, plan and select allowed tools; they cannot directly mutate core state outside application services.
9. Consequential actions require user approval and an authorization token scoped to the action, amount, target and expiry.
10. Outcome verification writes a ledger event with provenance and evidence.

## 4. Data and consistency

- PostgreSQL is the initial system of record for transactional data.
- Monetary values are stored as integer minor units plus ISO currency code, or NUMERIC with strict exponent validation. Never use binary floating point for money.
- Every financial record has an owner/tenant scope, provenance, timestamps and lifecycle state.
- Use database constraints and transactions for invariants that must survive concurrent requests.
- Use optimistic concurrency or row locks for contested updates.
- Use idempotency keys for user commands and external calls.
- Use a transactional outbox for reliable event publication; do not publish before the database transaction commits.
- Use a graph store only when graph query patterns justify it. The graph model is a domain concept first; an early version can live in PostgreSQL relational tables.
- Vector search is for retrieval, not authoritative transaction state or numeric calculations.
- Redis and distributed streaming infrastructure are added only when measured workload requires them.

## 5. AI/agent architecture

- Separate probabilistic interpretation/planning from deterministic execution.
- Agents receive least-privilege tools and task-scoped context, not unrestricted database access.
- Every tool has typed input/output schemas, authorization rules, timeout, retry policy and audit record.
- Tool outputs carry provenance, timestamps and evidence references.
- External content is untrusted input; it cannot override system policy or authorization.
- Use explicit workflow state machines for long-running missions. Persist checkpoints, attempts, deadlines and resumable progress.
- Require human approval for money movement, binding contracts, applications, disclosure of personal data or other consequential actions.
- Distinguish suggestion, attempted action, accepted action and externally verified outcome.

## 6. Privacy and security

- Private by default; purpose-specific, revocable consent.
- Store the minimum data required for a feature and define retention before collecting it.
- Keep identity, personal finance, skills, evidence and collective aggregates logically separated.
- Commons receives only the minimum approved aggregate signal; it must not expose raw personal records.
- Encrypt transport and storage; secrets only in environment/secret manager.
- Audit access, consent changes, agent tool calls and consequential actions.
- Add threat modelling, dependency scanning, static analysis and security tests as integrations are introduced.

## 7. Current implementation boundary

Iteration 00 provides an HTTP service, health endpoints and a pure deterministic cashflow calculation slice over caller-supplied data. It has no database, authentication, bank connections, agent runtime, Commons network or third-party actions. Those are deliberately excluded rather than represented by pretend integrations.
