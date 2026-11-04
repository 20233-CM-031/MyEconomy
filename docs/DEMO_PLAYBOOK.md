# MyEconomy Synthetic Demo Playbook v1.0

**This playbook uses fictional fixtures only.** A successful demo proves software behavior against controlled scenarios, not a live customer's outcome, real partner quote, government entitlement or actual payout.

## Demo cast

- One primary synthetic user: `CUS00001` for the personal-first journey.
- Guardian case: `GUA00001`, bill `BIL00004`, customer `CUS00002`.
- Commons quorum: `CAM00001`, five consented fictional participants: `CUS00003`, `CUS00004`, `CUS00012`, `CUS00013`, `CUS00065`.
- Agent checkpoint/resume: `MIS00002` with six ordered step fixtures.
- Negative net-value control: `OFF00088` from `api_scenarios/05_offer_net_value_rejection.json`.

## 1. Day-one Personal Power (one user)

1. Load `CUS00001` profile, budgets, goals, recent transactions and bills.
2. Show cashflow/obligations from the supplied sample records. Keep exact monetary arithmetic in `Decimal` or integer minor units.
3. Show potential actions and a source/evidence trail; ask the user what to do.
4. Explain that the user gets value before a Commons network or bank integration exists.

**Acceptance:** one user is enough; no Commons, bank connection or real provider action is needed. Label any inferred amount as an estimate until independently verified.

## 2. Guardian: bill evidence review

1. Open `source_documents/invoices_pdf/BIL00004_synthetic_invoice.pdf` or the HTML equivalent.
2. Extract document facts with the selected multimodal model; retain the page/region evidence and raw extraction confidence.
3. Compare line items and totals against `bills.csv` and `bill_line_items.csv` using deterministic arithmetic.
4. Load `GUA00001`; present the anomaly as a *potential billing issue*, not a proven scam or legal violation.
5. Draft a complaint/review message and stop at an approval boundary. Do not submit it to any real party.

**Acceptance:** source-grounded evidence; arithmetic reconciliation; false-positive-safe language; explicit approval required for submission.

## 3. Entitlement and Opportunity

1. Load a benefit assessment in `benefit_assessments.csv` and its fictional programme in `benefit_programs.csv`.
2. Display `POTENTIAL_MATCH` as a screening result only. The programme is `DEMO-*`, not a government scheme; no application is submitted.
3. Load a customer's skills and one or more `opportunity_matches`.
4. Show match rationale, missing evidence and the next user-controlled step.

**Acceptance:** every result has a rule/evidence explanation; no unsupported promise of eligibility, job placement or income.

## 4. Commons with five people

1. Open `api_scenarios/03_collective_commons.json`.
2. Show the five participating customers and verify that their `COMMONS_DEMAND_AGGREGATION` consent was valid on the signal date `2026-10-20`. A later withdrawal does not retroactively falsify a valid historical signal, but no new signal may be created after revocation.
3. Aggregate only the allowed dimensions: service category, city/locality cluster, quantity band and price band.
4. Show quorum 5/5 reached for `CAM00001`.
5. Show candidate offer `OFF00004`. Its provider, terms and sponsor are synthetic. The offer's arithmetic is positive under the fixture's net-benefit rule, but it is not a real quote or fulfilment commitment.
6. Show a second gathering campaign below quorum and explain that no provider quote should be requested yet.

**Acceptance:** no raw transaction, exact income, contact detail or individual hardship is exposed to a provider. Membership does not imply consent. Only event-time consent is considered for historical signals.

## 5. Reject a harmful offer

Load `api_scenarios/05_offer_net_value_rejection.json`. For each candidate calculate:

`net benefit = discount + sponsor credit - required incremental spend - fees - recurring commitment cost`

Reject `net benefit <= 0`, and also reject unresolved material conditions. Do not let provider commission influence the user's ranking. This is deterministic decision logic; a language model should only explain the result.

## 6. Agent checkpoint and resume

Load `api_scenarios/04_agent_checkpoint_resume.json` and `MIS00002`.

- Verify steps 1–4 against persisted fixture state/checkpoint hashes.
- Resume at the first incomplete step only after checking the external-side-effect state.
- Use each step's idempotency key. Do not replay a completed side effect.
- Request human approval only when the next action is consequential.

All side effects in this scenario are marked simulated and not sent.

## 7. Crisis, Shield and enterprise

Use `crisis_cases.csv`, `risk_signals.csv`, `micro_enterprises.csv`, `enterprise_products.csv`, `enterprise_orders.csv`, `skills.csv`, and `resource_listings.csv` to demonstrate:

- safe prioritization and relief discovery without reflexively pushing a new loan;
- risk explanation with evidence and uncertainty, not a definitive fraud declaration;
- skill/time/capacity matching to a paid project or teaching/service possibility;
- a one-person business catalogue and a simulated order-to-profit workflow.

Do not imply that an insurance claim, tax filing, benefit application, business order or payment reached a real institution.

## 8. Value ledger

`value_events.csv` is fixture output. Every row has `verification_level=SYNTHETIC_FIXTURE_ONLY`; it must not appear in a real-world impact KPI or be counted as realized VIVC. In a live customer system, VIVC needs an evidence item, baseline, source/provenance, outcome state and incremental-cost subtraction.

## Suggested judging story

1. Start with one person and immediate value (impact).
2. Show model understanding of a real-looking synthetic bill, grounded in evidence (Meta AI tooling).
3. Show exact deterministic calculations, access control, event-time consent and checkpointed agent execution (technical depth).
4. Add five-person Commons quorum and reject an economically bad offer (demo differentiation).
5. Close by distinguishing the capabilities running today, fixture simulations and the future live integrations.

## Persisted financial data — one-person foundation (Iteration 02)

This scenario proves that the financial data is not merely displayed from a static mock. It is imported through the actual authenticated API/application/domain/database path.

1. Start the app with migrations applied and an existing local user whose email is verified.
2. Set `APP_ENV=demo` and run `python scripts/seed_synthetic_customer.py --user-email <existing-verified-local-user> --customer-id CUS00001`.
3. Show the two user-owned synthetic accounts and their persisted transaction records.
4. Query `/api/v1/financial/cashflow` for a date range and one currency. Explain that only POSTED entries count; refunds offset expenses; transfers/ignore/pending are handled separately.
5. Run the loader again and demonstrate idempotency: accounts/obligations are reused and the same import batches replay without adding duplicate rows.
6. Show a rejected statement row and an external-reference conflict in a separate test persona/account; the rejected batch inserts zero transaction rows.
7. Import a transaction as `PENDING`, then import the same provider reference as `POSTED`; show `updated_count=1`, the audit event and the new cashflow effect. Attempt to reactivate a `REVERSED` transaction and show the application and database trigger reject it.
8. Upload a statement without a treatment column and show the credit is stored as `IGNORE`, not falsely counted as salary. A user-reviewed classification workflow is a later iteration.

The person whose existing verified local account is used is a demo operator identity, while `CUS00001` remains a synthetic fixture persona. No synthetic user login is created. This demonstrates local functional behavior only; no real bank connection or externally verified financial outcome is claimed.
