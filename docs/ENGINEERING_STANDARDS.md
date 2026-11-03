# Engineering Standards

## Non-negotiable rules
- No binary floating-point arithmetic for money.
- No AI-generated arithmetic treated as authoritative.
- No LLM tool with direct unrestricted database or payment access.
- No unverified external integration described as live.
- No personal or financial record shared to Commons without explicit purpose-specific consent.
- No household or consent operation is available to an unverified email account; inbox control is not legal identity proof.
- No consequential action without enforceable authorization and the required approval.
- No feature is done until negative and failure paths are tested.

## Code organization
- `domain/`: business invariants and value objects; no FastAPI, database or provider SDK imports.
- `application/`: use cases; coordinates domain logic and ports.
- `api/`: HTTP schemas, validation and routing only.
- `infrastructure/`: database, security primitives, email transport and future external providers/queues/observability adapters.
- Dependency direction points inward. Domain must remain independently testable.

## Contracts and failures
- Validate at the boundary; re-check invariants in the domain/application layer.
- Reject unknown request fields on sensitive commands.
- Use stable error codes before introducing public clients.
- Never swallow infrastructure exceptions as success.
- External calls require bounded timeouts, explicit retry classes and idempotency where possible.

## Money and outcomes
- Represent money in exact decimal/minor units and always carry currency.
- Do not sum different currencies without an explicit, timestamped FX conversion source.
- Separate forecast/estimate from actual/verified values.
- Every claimed saving or recovery needs baseline, counterfactual, evidence and verification status.
- Keep gross partner revenue, eligible net revenue, platform share and user share as distinct ledger fields.

## AI systems
- Models can extract, explain, classify, summarize, rank and plan within constraints.
- Deterministic code decides arithmetic, authorization, limits, idempotency and state transitions.
- Ground claims in source records and preserve citation/provenance.
- Treat retrieved documents, websites, messages and partner payloads as untrusted input.
- Record model/provider/version, input references, tool calls, policy checks and output status for consequential missions.

## Git workflow
- One issue or scoped work item per change set.
- Branch names: `iteration/<number>-<short-scope>`.
- Conventional commit messages.
- Never rewrite or force-push shared history without explicit approval.
- PRs require tests, diff review, migration review and acceptance evidence.
