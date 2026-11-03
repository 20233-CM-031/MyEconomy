# Synthetic Demo Dataset v1.0.0

## Purpose

A deterministic, relational, multi-format fixture corpus for engineering and demonstrating the MyEconomy product vision. It supports financial calculations, evidence extraction, Guardian workflows, benefit and opportunity matching, household consent, crisis/risk scenarios, one-person enterprise, agent checkpoint/resume, collective demand aggregation and a synthetic value ledger.

**This is not a real customer base.** Every person, household, provider, account, transaction, scheme, offer, claim, business, order, agent action and outcome is fictional. The app must retain a visible `SYNTHETIC DEMO` label whenever these records are used.

## Canonical path

`demo_data/synthetic_v1/`

The corpus contains **42 entity tables and 17,425 entity rows**, including 120 fictional customers, 55 households, 840 consent records, 225 accounts, 11,538 transactions, 240 bills and 523 bill lines, 39 loans and 334 amortization installments, 360 benefit assessments, 242 skill records, 80 opportunities, 90 offers, 44 demand signals, six Commons campaigns, eight agent missions and 59 mission steps.

## Formats and artifacts

- `csv/`: 42 entity tables, one CSV per table.
- `json/`: complete JSON arrays per entity table.
- `jsonl/`: one JSON object per line for stream ingestion and retrieval tests.
- `sql/schema.sql`, `sql/seed.sql`: PostgreSQL-oriented DDL and seed data (generated for PostgreSQL 15+; not yet executed against a live PostgreSQL server).
- `sqlite/myeconomy_synthetic_demo.sqlite3`: ready-to-query local fixture DB with 42 entity tables and `dataset_metadata`; primary keys, foreign keys, indexes and consistency checks.
- `source_documents/`: 240 synthetic HTML bills, 12 synthetic PDFs, 12 rendered PNG invoice pages and 90 fictional offer-term pages.
- `api_scenarios/`: five end-to-end scenario payloads.
- `metadata/`: schema catalog, data dictionary, business rules, regulatory controls, dataset profile, independent validation reports and SHA-256 manifest.
- Generator, Commons scenario override, SQLite builder, multimodal document builder and independent validator scripts.
- `DEMO_PLAYBOOK.md`: guided judge demo sequence.
- `REGULATORY_AND_DATA_RULES.md`: India-oriented engineering control mapping, not legal advice or certification.

## Product coverage

| Product capability | Dataset support |
|---|---|
| Day-One Personal Power | Customer context, income/expense histories, budgets, goals, bills and recurring obligations |
| Guardian | Bills, line items, evidence docs, anomaly cases and draft-only actions |
| Opportunity Engine | Skills, time/availability, opportunities and matches |
| Benefits / Entitlements | Fictional programs, assessments and application-state fixtures |
| Resource Exchange | Resource listings, supply/demand and availability-like fields |
| Crisis Shield | Crisis cases, cashflow stress and relief/opportunity fixtures |
| Knowledge-to-Economic-Asset | Evidence-backed skills and opportunity links |
| Economic Defence | Risk signals with evidence, confidence and safe-action hints |
| One-Person Enterprise | Enterprises, products, catalogues and simulated orders |
| Commons | Purpose-consented demand signals, participants, quorum campaign and matched candidate offer |
| Agent reliability | Missions, step sequence, checkpoints, idempotency and resume fixtures |
| Value Ledger | Estimated/simulated/verified-state examples; all supplied events are synthetic only |

## Important designed cases

- `CAM00001`: five fictional participants with `COMMONS_DEMAND_AGGREGATION` consent valid at each signal timestamp, in one broad Jaipur locality cluster. It reaches the fixture quorum of 5/5 and points to matching fictional education offer `OFF00004`. No real provider bid, sponsor funding, contract, service delivery or payout exists.
- The offer arithmetic includes discount, sponsor credit, incremental spend, fees and recurring commitment; a candidate is not recommended if net benefit is non-positive.
- A harmful/negative-net-benefit offer exists as a rejection scenario.
- Agent missions include completed steps, an interruption and a resumable checkpoint; these are fixtures, not a real autonomous runtime.

## Reproduction and validation

From this folder, with Python 3.12+:

```bash
python generate_synthetic_dataset.py --out ./generated_v1 --customers 120 --seed 20261103
python create_multimodal_samples.py ./generated_v1
python apply_demo_scenario_overrides.py ./generated_v1
python build_sqlite.py ./generated_v1
python validate_dataset.py ./generated_v1
```

The already included PDFs/PNGs and SQLite database are ready for use; generation is only needed to reproduce or modify the fixtures. `validate_dataset.py` checks primary keys, foreign keys, synthetic labels, invalid contact placeholders, excluded identity secrets, transaction direction, bill totals, offer arithmetic, consent at event time, Commons privacy/quorum/linkage, VIVC synthetic status, PDF/PNG hashes, export parity and SQLite integrity.

## Data and legal boundaries

- No deliverable email address or valid phone number is present; contacts use `.invalid` and deliberately invalid phone placeholders.
- No actual Aadhaar/PAN numbers, card PAN, UPI PIN, bank password, payment credential or authentic account identifier is included.
- Benefits/programs are fictional and a potential match is not an official eligibility result.
- Providers, offers, claims, applications, orders, settlements, agent actions, savings and value events are simulated.
- Commons signals include only approved broad service/location/quantity/price bands, not raw transactions, income or account data.
- Consent is evaluated at event time. Later revocation affects later use; it does not rewrite whether an earlier event was authorized at its recorded timestamp.
- Data is not to be used to contact or transact with a real provider, bank, insurer, government authority or customer.

## Money semantics

Money values in CSV/JSON/JSONL/SQL fixtures are decimal strings. Use `Decimal` or integer minor units; never IEEE-754 binary floating point. Transactions distinguish income, expense, refund, transfer and ignored movements to avoid double-counting. Loan schedules are amortization fixtures. Offer net value is:

`discount + sponsor credit - incremental spend - fees - recurring commitment cost`

## Honest demo rule

Show actual software behavior against deterministic fixtures. Label each fixture and every simulated external response. Do not claim that a refund, scholarship, provider quote, sponsor credit, job, order, loan, payment or payout happened in the real world unless an external authoritative system independently confirms it.
