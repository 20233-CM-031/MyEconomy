# AI Collaboration and Repository Memory Protocol

This document explains how future ChatGPT/AI engineering sessions must use GitHub and repository files as project context.

## 1. Repository is the durable project memory

Use `https://github.com/20233-CM-031/MyEconomy` as the shared source of truth. Chat messages explain intent and provide context, but source code, tests, decisions and repository memory documents determine what exists and what was decided.

At the start of every engineering session, read `docs/AWNNORA_CONTEXT_MAP.md` first. The system identity is AwnNORA; preserve the separate roles of MAKOS (operational workspace), GENIEA (agent orchestration) and KRN (knowledge/relationship architecture).

At the start of every engineering session:

1. Read current repository metadata, default branch, branches and latest commits.
2. Inspect the root tree and current status/working diff where access permits.
3. Read `AGENTS.md`, `README.md`, `docs/PROJECT_MEMORY.md`, `docs/PROJECT_STATUS.md`, `docs/FEATURE_CATALOG.md`, `docs/CODEBASE_MAP.md`, `docs/THREAT_MODEL.md` and `docs/HACKATHON_SCORECARD.md`.
4. Read the relevant feature specification, latest iteration record and ADRs.
5. Fetch actual code and tests for every module that may be changed.
6. Compare repository state with the last known conversation state; call out drift instead of silently assuming.

Do not assume the GitHub connector has write permission. If remote writes fail, state the exact error and provide a patch/archive and user-executable Git commands. Never claim a remote push succeeded without confirmation.

## 2. Working model and terminology

- Product: AwnNORA (confirmed). Repository/package implementation base: MyEconomy.
- Product category: Personal Economic Agency & Collective Opportunity Intelligence.
- Personal Mode: standalone first-day value, even for one user.
- Commons Mode: consent-controlled collective demand/resource/opportunity coordination.
- Eight pillars: Guardian, Opportunity, Entitlement/Benefits, Resource Exchange, Crisis Shield, Knowledge-to-Economic-Asset, Economic Defence, One-Person Enterprise.
- Architecture terms MAKOS, GENIEA and KRN refer to the larger product-system concepts captured in `PROJECT_MEMORY.md`; they are target concepts, not existing code modules in Iteration 00.
- AI is not authoritative for money, identity, eligibility decisions, authorization or verified outcomes.

## 3. File-level change manifest is mandatory

For every delivery, report each added/modified/deleted file with:
- exact repo-relative path;
- change type;
- reason and responsibility;
- main symbols, routes, schema, data model or workflow introduced/changed;
- dependencies and integration points;
- tests and acceptance criteria;
- migration/rollback considerations;
- exact Git commands to add, commit and push.

If more than a handful of files are changed, also generate `docs/CHANGELOG/` or an iteration-specific change record. Do not merely give the user a ZIP without explaining where its contents belong.

## 4. Git workflow

Preferred workflow:

```bash
git status --short --branch
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c iteration/NN-short-scope
# apply/copy reviewed files at their exact paths
git diff --check
# run tests, lint and runtime checks
git add <explicit paths>
git commit -m "feat: <scoped capability>"
git push -u origin iteration/NN-short-scope
```

Then create a pull request into `main`, review diff/CI, and merge only after acceptance. Do not push directly to `main` unless the user explicitly requests that workflow. Do not force push. If a supplied patch targets a different base revision, inspect it and regenerate rather than applying blindly.

## 5. Engineering implementation rules

- Start with the user story, scope and acceptance criteria; don't start by generating code.
- Draw the sequence/data flow and identify trust boundaries before implementing complex workflows.
- Keep domain logic framework-independent and deterministic.
- Define contracts, invariants, error states, authorization, idempotency, retries and observability before external integrations.
- Separate model planning from tool execution and state mutation.
- Use typed tool contracts and minimal scopes. External content is untrusted.
- Persist durable workflow state and checkpoints for long-running missions; resume after interruption without repeating completed side effects.
- Use a database as system of record; transactions, constraints and outbox for consistent state/event publication.
- Use migrations, rollback plans, seed/fixture strategy and realistic integration tests.
- Avoid microservices until independently justified; maintain strict modular monolith boundaries.
- Avoid vector/graph stores until query/use-case requirements justify them. A graph may begin as a well-designed relational model.
- Don't add an abstraction or dependency without explaining the concrete requirement it serves.

## 6. Documentation update contract

After a meaningful code change, update as applicable:
- `PROJECT_STATUS.md`: current actual state, commit, tests, blocker, next step.
- `CODEBASE_MAP.md`: files, symbols, call paths, dependencies and tests.
- `FEATURE_CATALOG.md`: exact feature status and evidence.
- `PROJECT_MEMORY.md`: only durable changes in product intent, architecture or principles.
- relevant ADR: architecture decision and consequences.
- iteration record: scope, acceptance, test results, known limitations.

Do not duplicate every line of code into memory docs; document symbols, contracts, invariants, call graph and the source path. The code and tests remain the line-level authority. Keep docs navigable and update stale descriptions.

## 7. Accurate status vocabulary

Use these labels precisely:
- **Implemented and tested:** code exists and relevant tests passed in the stated environment.
- **Implemented, not fully verified:** code exists but required tests/runtime checks are missing.
- **Partial:** some acceptance criteria are satisfied.
- **Designed:** architecture/requirements only, no working implementation.
- **Simulated:** fixture/mock/demo behavior, never real integration.
- **Blocked:** cannot progress because of a named dependency, permission or external capability.

Never equate a mock endpoint, successful LLM response or attractive UI with a functioning end-to-end feature.
