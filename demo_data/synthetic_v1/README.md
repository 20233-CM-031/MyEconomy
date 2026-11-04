# MyEconomy Synthetic Economic Demo Dataset v1.0.0

**Snapshot:** 2026-11-03  
**Deterministic generation seed:** `20261103`  
**Customers:** 120 fictional adults  
**Households:** 55  
**Transactions:** 11,538  
**Entity tables:** 42  
**Total entity rows:** 17,425  
**Synthetic-only:** yes

> This is a realistic, relational test/demo fixture dataset. It is not real customer information, real bank data, real providers, government benefits, official eligibility, actual offers, actual activity or evidence of product impact. All records are fictional and labelled `SYNTHETIC_FIXTURE`.

## Formats included

- `csv/`: one CSV per entity table.
- `json/`: one complete JSON array per entity table.
- `jsonl/`: one JSON object per line, suitable for streaming/ETL and retrieval tests.
- `sql/schema.sql` and `sql/seed.sql`: PostgreSQL-oriented schema and deterministic seed (PostgreSQL 15+ target; no live server was used for this package verification).
- `sqlite/myeconomy_synthetic_demo.sqlite3`: ready-to-query SQLite database with 42 entity tables plus `dataset_metadata`, primary keys, foreign keys and indexes. Values are intentionally stored as text to preserve exact decimal strings and original source representation.
- `source_documents/invoices/`: synthetic HTML bills.
- `source_documents/invoices_pdf/`: 12 synthetic PDF invoices.
- `source_documents/invoices_png/`: rendered PNG invoice pages for image/multimodal ingestion.
- `source_documents/offer_terms/`: fictional offer/terms documents for RAG and evidence tests.
- `api_scenarios/`: coherent demo journeys for day-one value, Guardian, Commons quorum, checkpoint/resume and negative-net-benefit rejection.
- `source_documents/guardian/` + `guardian_workflow/`: additive Iteration 04 Guardian API scenario, with three fictional bills, manually structured payloads, verified page/line/column locators, a local API runner and SHA-256 file manifest. These supplemental files do not change the 42 relational tables / 17,425-row v1.0.0 core corpus.
- `metadata/`: schema catalog, relationships, data dictionary, business rules, regulatory-control notes, document hashes and validation reports.
- `generate_synthetic_dataset.py`: deterministic fixture generator.
- `apply_demo_scenario_overrides.py`: applies the intentionally designed five-person Commons quorum scenario and honest no-quote states for other campaigns.
- `build_sqlite.py`: rebuilds the SQLite database from CSV exports.
- `create_multimodal_samples.py`: recreates synthetic invoice source documents (requires its documented Python PDF dependency).
- `validate_dataset.py`: independent referential-integrity and business-rule validator.

## Core fixture coverage

| Product area | Representative records |
|---|---|
| Personal finance | Customers, households, 225 accounts, 11,538 transactions, budgets, envelopes, goals |
| Obligations and credit | 531 recurring obligations, 39 fictional loans, 334 amortization installments, 36 tax reminders |
| Bills and Guardian | 240 bills, 523 line items, 67 Guardian cases/evidence records, 12 multimodal PDF/PNG examples |
| Protection and crisis | 42 risk signals, 28 crisis cases, 52 insurance policies and 18 simulated claims |
| Benefits | 12 fictional programmes, 360 assessments and 64 non-submitted application fixtures |
| Opportunity and skills | 242 skill records, 80 opportunities and 116 matches |
| One-person enterprise | 35 fictional micro-enterprises, 105 products and 130 simulated orders |
| Resource exchange | 15 capacity/resource listings |
| Commons | 44 purpose-consented demand signals, 6 campaigns and 13 participant links; `CAM00001` is a synthetic 5/5 quorum scenario |
| Agents and audit | 8 missions, 59 steps/checkpoints, 360 audit events |
| Value ledger | 45 events, all `SYNTHETIC_FIXTURE_ONLY`; never count as actual VIVC |

## Reproduce the exact dataset

From this folder, using Python 3.12+:

```bash
python generate_synthetic_dataset.py --out ./generated_v1 --customers 120 --seed 20261103
python create_multimodal_samples.py ./generated_v1
python apply_demo_scenario_overrides.py ./generated_v1
python build_sqlite.py ./generated_v1
python validate_dataset.py ./generated_v1
```

`create_multimodal_samples.py` requires ReportLab. The package already includes the generated PDF/PNG samples, so these steps are only needed when reproducing the corpus from scratch. PNG re-rendering is a separate PDF-rendering step; the included PNGs are ready for demo ingestion.

## Safety and event-time consent

- Customer contacts use `example.invalid` and intentionally invalid `+91-00000-xxxxx` phone placeholders.
- There are no Aadhaar, PAN, card PAN, UPI PIN, passwords, bank credentials or real account numbers.
- Broad city/locality clusters are not home addresses.
- Consent is evaluated at the event timestamp, not merely by the current status label. A later revocation stops future use but does not rewrite whether an earlier event was authorised at its time.
- Household membership never grants financial data access.
- Commons demand carries only service category, broad location cluster, quantity band and price band. No raw transactions or exact incomes are included.
- Benefits are fictional; `POTENTIAL_MATCH` is not an official eligibility decision.
- Provider offers, sponsor funding, orders, claims, applications, settlements, agent actions and value events are simulated.
- No action should be sent to a real external provider, bank, insurer, government authority or payment system.

## Money and calculations

Money is represented as decimal strings to avoid binary floating-point loss in CSV/JSON/SQL fixtures. Parse with `Decimal` or use integer minor units in production. Transactions distinguish `INCOME`, `EXPENSE`, `REFUND`, `TRANSFER` and `IGNORE` so card purchases and card repayments are not counted as two independent expenses. Loan installments follow a synthetic amortization schedule. Offer net benefit is calculated as:

`discount + sponsor credit - incremental spend - fees - recurring commitment cost`

Net benefit at or below zero is rejected; unresolved material terms also require rejection or human review.

## Legal and regulatory note

`REGULATORY_AND_DATA_RULES.md` documents an India-oriented engineering mapping as of 2026-11-03, including the staged commencement of the DPDP Act/Rules, RBI Account Aggregator consent constraints and conditional digital-lending controls. It is not legal advice or a compliance certification. Check official notifications and obtain legal review before live processing.


## Load a single fixture persona into the application

From the repository root, with migrations applied and an existing active email-verified local user:

```powershell
$env:APP_ENV = "demo"
python scripts/seed_synthetic_customer.py --user-email "existing-verified-local-user@example.invalid" --customer-id CUS00001
```

The script refuses `APP_ENV=production`, never creates a login identity, and only loads rows explicitly marked `SYNTHETIC_FIXTURE`. It imports accounts, transaction rows and recurring obligations through the application's persistence/domain services. Stable source IDs and idempotency keys make reruns safe. It does not import the rest of the future-feature fixture tables into application runtime yet.


## Guardian invoice workflow add-on (Iteration 04)

The separate `source_documents/guardian/` directory contains a prior-period broadband bill (INR 800), a later bill with a higher amount (INR 1,180) and a deliberately inconsistent installation invoice. The legal entity, person and all amounts are invented. `guardian_workflow/invoice_payloads.json` provides manual structured request bodies and source locators for the API workflow. The locators were checked against `pdftotext -layout` output; `metadata/guardian_workflow_manifest.json` stores each PDF's SHA-256 and size.

Run `guardian_workflow/run_demo.py` against a local development instance and a dedicated verified demo user. The uploaded files remain `STORED_UNSCANNED`; no malware scan, OCR, Meta AI model extraction, automated provider contact or actual financial event occurs. The demo script creates review cases and drafts but leaves them awaiting a human decision.
