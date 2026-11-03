# Synthetic Demo Dataset v1.0.0 — Delivery Record

**Date:** 2026-11-03  
**Status:** Generated and independent validation passed  
**Nature:** Demo/test fixtures only; not a production customer dataset.

## Reconciled corpus

- 42 entity tables; 17,425 rows.
- 120 fictional adult profiles; 55 households; 840 purpose-scoped consent records.
- 225 accounts and 11,538 transaction fixtures across Jan–Oct 2026.
- 240 bills, 523 line items and 12 PDF / 12 PNG invoice samples.
- 39 loans, 334 installments, 531 recurring obligations and 75 subscriptions.
- 360 benefit assessments; 242 skill records; 80 opportunities; 116 opportunity matches.
- 90 offers; 15 resource listings; 44 Commons demand signals; six campaigns.
- Eight agent missions and 59 mission steps; 67 Guardian cases/evidence records; 45 synthetic value events.
- 28 crisis cases; 42 risk signals; 35 micro-enterprises; 105 products and 130 simulated orders.

## Canonical files

All data files reside under `demo_data/synthetic_v1/`:

| Path | Purpose |
|---|---|
| `csv/` | Relational export, one file per entity table |
| `json/` | Whole-table JSON exports |
| `jsonl/` | Streaming / ETL-friendly row-oriented exports |
| `sql/schema.sql` | PostgreSQL-oriented DDL |
| `sql/seed.sql` | PostgreSQL-oriented deterministic seed |
| `sqlite/myeconomy_synthetic_demo.sqlite3` | Embedded relational fixture database |
| `source_documents/invoices/` | Synthetic invoice HTML |
| `source_documents/invoices_pdf/` | Synthetic invoice PDFs |
| `source_documents/invoices_png/` | Rendered invoice pages for multimodal extraction |
| `source_documents/offer_terms/` | Fictional provider offer terms |
| `api_scenarios/` | Five demo request/mission payloads |
| `metadata/` | Catalog, dictionary, rules, controls, hashes, profiles and reports |
| `DEMO_PLAYBOOK.md` | Judge workflow and narrative |
| `REGULATORY_AND_DATA_RULES.md` | India-oriented control mapping and caveats |

## Key deterministic demo

`CAM00001` has a synthetic five-person Jaipur education cohort. Each demand signal has purpose-specific consent valid at the signal timestamp. The campaign reaches 5/5 fixture quorum and references the matching simulated offer `OFF00004`. No real provider quote, sponsor agreement, service fulfilment or payment exists.

## Validation evidence

The final independent validator passed 111 checks, including:
- unique entity primary keys and all catalogued foreign-key links;
- explicit synthetic labels and non-deliverable contact placeholders;
- absence of direct identity credentials;
- transaction sign/direction and positive amount rules;
- bill-line arithmetic reconciliation;
- offer net-benefit arithmetic and decision classification;
- event-time Commons consent and no raw-financial-data disclosure;
- campaign quorum and candidate-offer category/city match;
- synthetic-only value-event labels;
- PDF/PNG SHA-256 match and magic bytes;
- CSV/JSON/JSONL count parity;
- SQLite `integrity_check=ok`, zero foreign-key violations, 42 tables and 17,425 rows.

PostgreSQL DDL/seed are supplied but not claimed as live-server-tested. SQLite is the verified local fixture database.

## Product and hackathon usage

The corpus supports a coherent presentation of Personal Mode working for a single person and Commons Mode scaling to a consented cohort. It is intentionally not evidence of live external integrations. Use it to demonstrate parsing, deterministic calculation, policy enforcement, orchestration, audit and simulation; do not label synthetic events as real user impact or verified VIVC.
