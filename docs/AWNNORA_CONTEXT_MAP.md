# AwnNORA — Canonical Product and Engineering Context Map

**Canonical project name:** AwnNORA
**Implementation repository:** `20233-CM-031/MyEconomy`
**Context-map version:** 1.1
**Reconciled:** 2026-11-04
**Status:** Product vision confirmed; Iterations 00–03 merged (PR #3); Iteration 04 Guardian API vertical implemented locally and tested, not yet pushed.

> This document resolves older working-name language in historical notes. AwnNORA is the project/product name for the Meta Global AI Hackathon. `MyEconomy` remains the existing repository and Python package name because it is the implementation base. It is not an alternative product brand.

## 1. The system in one sentence

**AwnNORA is a Human Economic Intelligence System:** it gives each person a private AI representative that protects their interests, finds ways to reduce burdens, unlocks income and benefits, helps create enterprises, and—only with explicit permission—connects people's needs and resources into collective economic power.

The goal is not to maximize conversations, screen time, ad impressions or transactions. The goal is to improve real people's economic agency and measure the verified value created.

## 2. The problem being solved

Households and individuals face fragmented financial information, weak bargaining power, limited time to discover opportunities, difficulty navigating benefits and services, and no persistent system representing their interests across providers and institutions.

The broader economy also contains fragmented demand, fragmented supply, underused resources, information asymmetry and high coordination costs. Examples include available tutor hours, unused vehicle seats, surplus produce, idle equipment, warehouse capacity, unused institutional facilities and funding that struggles to reach eligible recipients.

AwnNORA addresses both sides:

1. **Individual agency:** understand a person's circumstances and act on their priorities.
2. **Collective intelligence:** connect approved demand with suitable supply, opportunities, funding and capacity without exposing private records.

## 3. Product principles

- **Day-One value:** Personal Mode must work for one person; network scale is an advantage, not a prerequisite.
- **Personal first, collective by choice:** Commons participation is optional, purpose-specific and revocable.
- **Protect and empower:** lower outflow, increase legitimate inflow, unlock external value and protect stability.
- **Evidence before confidence:** extracted facts point to source evidence; low confidence causes review or abstention.
- **Deterministic economic truth:** money arithmetic, eligibility constraints, permissions, net-value calculations, state transitions and outcome accounting are code-enforced.
- **Model-assisted intelligence:** models interpret, extract, explain, retrieve and plan; they do not become the source of truth for arithmetic, permissions or verified outcomes.
- **No invented impact:** potential, estimated, attempted, provider-confirmed and independently verified value are distinct states.
- **Privacy by design:** private records remain private; collective intelligence receives only approved and minimized signals.

## 4. The user experience: two modes

### Personal Mode — useful immediately

The user tells AwnNORA what matters: save money, recover something owed, earn more, find benefits, protect against loss, solve a specific problem, or start/grow a business. Optional context may include a document, skills, availability, upcoming commitments or imported financial data. Connecting a bank account is not mandatory for the first useful result.

The system produces a **Personal Power Report** with prioritized opportunities, evidence, missing information, confidence, expected effort and a safe next action. It should help complete at least one useful action during the first session where possible.

### Commons Mode — collective power

With separate consent, personal agents can contribute narrow purpose-specific demand or capacity signals. The network can discover collective purchasing opportunities, unused-resource matches, work and service opportunities, emergency resource coordination and funded benefits. Users do not have to expose their underlying financial history to participate.

## 5. Six connected economic capabilities

These are capability areas within one system, not six disconnected apps.

| Capability | Purpose | Example workflows |
|---|---|---|
| **Guardian / Economic Defence** | Protect interests and recover value | Invoice review, duplicate/incorrect-charge signals, refunds, warranty/compensation evidence, suspicious payment requests, complaint drafts, recurring contract review |
| **Opportunity & Entitlements** | Find legitimate income and benefits | Jobs, freelance projects, training linked to demand, scholarships, subsidies, grants, insurance/employer benefits and reimbursements |
| **One-Person Enterprise** | Help a person create and operate a business | Demand discovery, pricing, unit economics, catalogue/storefront, enquiries, orders, invoices and profitability |
| **Resource Exchange** | Match underused capacity with real demand | Tutor hours, skills, equipment, transport seats, surplus inventory, produce, storage, space and institutional capacity |
| **Commons** | Turn consented demand into collective leverage | Group purchasing, sponsor-funded concessions, supplier matching, demand aggregation, buyer/provider agent negotiation |
| **Crisis Shield** | Preserve stability when circumstances change | Cash-flow stress review, essential obligations, relief routes, verified assistance, community resource matching; never reflexively push loans |

Cross-cutting foundation: the **Household/Personal Economic Twin** — a time-aware model of income, obligations, services, commitments, skills, resources, goals, permissions, opportunities and verified outcomes.

## 6. Architecture: how the named systems fit together

```text
                         AWNNORA
          Human Economic Intelligence System

   Personal Mode                           Commons Mode
   Personal Power Report                   Collective opportunity network
          |                                         |
          +----------- Personal Agents -------------+
                            |
       +--------------------+---------------------+
       |                    |                     |
     MAKOS                GENIEA                  KRN
  Operational         Agent/mission         Knowledge and
  workspace &         orchestration          relationship
  workflow surface    and coordination       architecture
       |                    |                     |
       +--------------------+---------------------+
                            |
       Data Plane | Knowledge/RAG Plane | Logic & Intelligence
                            |
                 Agent & Automation Plane
                            |
              APIs / approved integrations / people
                            |
                 Evidence, settlement, outcomes
```

### MAKOS — operational workspace

MAKOS is the durable user/operator workspace for cases, tasks, documents, approvals, operational processes, financial and commercial workflows, enterprise administration and system visibility. It is where work is organized and acted upon. The AwnNORA user experience should make the state of a workflow visible: evidence, owner, next step, approvals, due dates, action history and outcome.

### GENIEA — agent orchestration and collective intelligence

GENIEA coordinates personal and specialist agents, creates bounded missions, selects approved tools, plans and sequences work, handles retries and interruptions, resumes from durable checkpoints, routes human approvals and coordinates agent-to-agent or personal-to-collective work. It never bypasses permissions, consent, domain services or audit.

The reliability target is to resume a long workflow from the last valid checkpoint rather than restarting from step one when a late step needs review. External side effects must be idempotent or reconciled before retry; exactly-once execution must not be claimed without a true provider guarantee.

### KRN — knowledge, evidence and relationship architecture

KRN is not merely a graph database. Its intended role is to maintain identity, relationships, provenance, evidence, temporal validity, context, retrieval structures, reasoning interfaces, capability links and controlled information flow. It supports both private knowledge partitions and explicitly permitted shared edges that form the Collective Opportunity Graph.

The supplied **KRN V1 — THE STORM** proposal is a research/design blueprint. It describes a layered data and intelligence substrate including KSDS/data structures, storage abstraction, semantic/hash addressing, query planning and algorithm selection, Data Genome, SuperRAG/SpiderCrawler, knowledge and reasoning planes, Flow Cortex/KFL, capability/simulation/verification/trace/memory/learning planes and DRCE. These are design concepts, not implemented runtime features in the current repository. Keep stable interfaces separate from replaceable data structures and algorithms; introduce novel algorithms only where comparative measurements show a real gap.

### Data and intelligence planes

- **Data Plane:** owner-scoped users, households, financial records, consent, files, evidence, transactions, event/outbox and integration provenance.
- **Knowledge/RAG Plane:** trusted retrieval across public rules, benefits, provider terms, product/service information and user-authorized documents. Every claim retains its source, version/date and evidence span. Retrieved text is untrusted input.
- **Logic & Intelligence Plane:** deterministic rules, money, eligibility, matching, ranking, forecasts, constraints, offer optimization and VIVC accounting.
- **Agent & Automation Plane:** typed tools, bounded missions, checkpoints, idempotency, retries, timeouts, approvals, replay/reconciliation and audit.
- **Orchestrator:** coordinates multi-plane work while preserving domain boundaries and authorization.
- **Meta AI layer:** use Meta models where they materially improve document understanding, multimodal perception, language reasoning, planning or agent interactions. Model choice is evaluated per task; no decorative integration.

### GENIEA-KRN architecture proposal mapping

The separate GENIEA-KRN proposal describes seven broad layers: sensors/inputs; memory and knowledge substrate; reasoning and cognition; execution and orchestration; safety and governance; presentation and output; platform and infrastructure. Map these to AwnNORA's input adapters, KRN knowledge substrate, model + deterministic reasoning, GENIEA missions, consent/policy/audit gates, MAKOS experiences and the data/deployment platform. This is a conceptual mapping, not a claim that all seven layers exist in the current code.

## 7. Collective Opportunity Graph

The graph connects:

- people and organizations;
- needs and demand signals;
- skills, capabilities and availability;
- supply, inventory and unused capacity;
- location, schedule, eligibility and constraints;
- offers, funding and sponsorship;
- permissions, trust evidence and commitments;
- settlement, user benefit and verified outcomes.

The network can discover combinations that no participant could find alone. Example: families need affordable tutoring; a verified educator has spare class capacity; another family needs the same subject; an approved sponsor has education credits. AwnNORA checks fit, availability, terms, consent and net value, then coordinates an opt-in arrangement.

The research challenge is not simply group buying. Group buying, referral and cashback already exist. The differentiated proposition to test is the combination of a personal economic model, privacy-limited multi-sided demand/supply matching, agent-mediated negotiation, deterministic net-value optimization and transparent distribution of verified value.

## 8. Economic value and business model

The proposed model monetizes value created by coordination rather than selling identifiable financial histories.

- Direct price discounts and earmarked subsidies: pass through 100% to the intended user/beneficiary.
- Eligible partner/affiliate/referral revenue: proposed 50/50 split of **defined eligible net revenue**, after agreed taxes, refunds, chargebacks and direct transaction costs.
- Partner subscriptions, institutional programmes, booking/service fees and transparent commercial sponsorship are potential revenue sources.
- Research/data-dividend participation is a separate, voluntary programme with separate informed consent and privacy controls; no guaranteed earnings promise and no sale of identifiable bank statements.
- Do not reward or incentivize invalid ad clicks or views. Sponsored offers must be assessed by user benefit, not platform commission.

### North-star: VIVC

`VIVC = verified money recovered + verified expenditure savings + additional verified earnings + benefits actually received + demonstrably prevented fees/penalties - additional costs incurred`.

VIVC must count only deduplicated, evidence-backed, settlement-verified, live outcomes. Estimated savings, synthetic fixtures, opportunities, applications and attempted actions are not verified VIVC.

## 9. Trust and safety invariants

1. Private by default; sharing requires explicit purpose, category, recipient and time scope.
2. Revocation blocks future reads/uses; access checks and data reads must share a transaction boundary where possible.
3. A household membership never implicitly grants access to another person's financial records.
4. Commons receives minimized, opted-in signals; no raw transaction or evidence-document export by default.
5. Minimum cohort thresholds are necessary but not sufficient: add anti-differencing, rare-attribute suppression, rate limits, privacy analysis and possibly differential privacy before production.
6. Evidence links point to a document hash and stable locator; extraction confidence is not proof.
7. Models and user documents are untrusted; resist prompt injection and fabricated claims.
8. Tools are typed and least-privilege. Mutating external actions require current permission, explicit approval, idempotency and audit.
9. Legal entitlement, benefit award, employment and provider action are confirmed only by the authoritative party.
10. Separate SYNTHETIC, SANDBOX and LIVE environments; never let demo data become production truth.

## 10. Repository reality — merged code and local candidate

Repository: `20233-CM-031/MyEconomy`, default branch `main`. Live GitHub inspection on 2026-11-04 verified `main` at `5b5cf669773d5c0cd33f5abffb8c46d44cead797`, the merge commit for PR #3 (Iteration 03).

| Area | Actual state |
|---|---|
| Iteration 00 | Merged: deterministic Decimal cashflow foundation/API |
| Iteration 01 | Merged: registration, verification, sessions, household boundaries, consent and append-only audit |
| Iteration 02 | Merged: owner-scoped financial accounts, bounded CSV ledger import, recurring obligations, persisted cashflow and DB guards |
| Iteration 03 | **Merged in PR #3:** deterministic invoice/evidence review, offer net-value, in-memory consent-aware aggregation, VIVC rules and GENIEA mission/tool policy kernel |
| Iteration 04 | **Local candidate:** authenticated Guardian evidence upload, private local storage adapter, persisted owner-scoped invoice review cases, evidence/hash metadata, audit, draft and explicit approval-state APIs |
| MAKOS workspace/UI | Not implemented; APIs and workflow foundations only |
| GENIEA durable runtime | Not implemented; only domain mission/tool policies exist, no persistent mission/step/checkpoint executor |
| KRN graph runtime | Not implemented; architecture documents define private/shared graph boundaries and evidence/provenance responsibilities |
| RAG / SpiderCrawler | Not implemented |
| Meta model gateway / OCR | Not implemented; Iteration 04 accepts user-submitted structured fields, not extracted model output |
| Live provider action | Not implemented; draft approval does not send a provider message |
| Production document store/scanner | Not implemented; Iteration 04 uses local private filesystem with `STORED_UNSCANNED` state |
| Bank aggregation, payments, partner settlement/payout | Not implemented |
| Persistent Commons marketplace | Not implemented; only domain-level in-memory aggregate and offer evaluation primitives |

Iteration 04 local verification: 84 tests pass on Python 3.13; Python compilation, SQLite migration upgrade/downgrade/re-upgrade and the existing synthetic dataset validator pass. Ruff and Python 3.12 were unavailable locally. Live PostgreSQL 16 testing of the new Guardian migration is pending. The three new Guardian PDFs are synthetic-only and have a separate hash/locator manifest.

### Iteration 04 real API path — precise boundary

`verified user -> bounded PDF/PNG/JPEG upload -> signature/size check -> SHA-256 -> owner-scoped metadata + local private blob -> STORED_UNSCANNED -> user-submitted structured invoice + evidence locators -> deterministic domain review -> persisted case/findings + audit -> draft -> explicit user approval state`

This path is API-accessible and covered by tests. It does not yet perform document scanning, OCR, source-locator verification, AI extraction, provider delivery or automated settlement. Evidence locator strings are submitted by the client and are not cryptographically/visually verified against page regions in this iteration. The local filesystem adapter is for a trusted development/demo host only.

## 11. GitHub and delivery state

Live read-only access confirms PR #3 merged to `main` at `5b5cf669773d5c0cd33f5abffb8c46d44cead797`. The connected GitHub identity is `20233-CM-031`, but the available GitHub App installation remains associated with `kareem1207`; its installation repository list excludes `20233-CM-031/MyEconomy`. A feature-branch creation attempt for Iteration 04 returned HTTP 403 `Resource not accessible by integration`. Available commit-status/workflow endpoints returned no CI records for the PR #3 merge SHA, so do not infer CI success from the empty response.

No Iteration 04 branch, commit or PR has been created remotely by this assistant. The Iteration 04 source tree is reconstructed from the complete project artifact and spot-checked against the merged Iteration 03 source; it is not a fresh Git clone. Before applying it, fetch `origin/main`, confirm the base SHA has not advanced, inspect the diff, run the full test/CI matrix, then push a feature branch. Never write directly to `main`.

## 12. Source hierarchy and handoff rules

For implementation state, live GitHub code/tests/migrations/CI outrank documentation. For confirmed product decisions, this map and the user's latest explicit instructions outrank older brand/name text in historical files. The uploaded `AwnNORA.txt` supplies the product direction; `Geniea_KRN_Kimi_Unified_AGI_Architecture_Proposal_v1.0.md` supplies a seven-layer GENIEA-KRN conceptual mapping; `KRN V1 — THE STORM` supplies the detailed KRN design blueprint.

Every iteration must update this map, `PROJECT_MEMORY.md`, `PROJECT_STATUS.md`, `CODEBASE_MAP.md`, `FEATURE_CATALOG.md` and an iteration record. Always report exact files, test commands, passed/failed checks, local-versus-remote status, and integrations that remain simulated or absent.
