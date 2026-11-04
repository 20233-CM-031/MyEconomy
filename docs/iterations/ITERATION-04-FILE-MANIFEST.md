# Iteration 04 File Manifest — Guardian Evidence & Invoice Review

**Base:** `main` at `5b5cf669773d5c0cd33f5abffb8c46d44cead797` (PR #3 merge).  
**Delivery:** local candidate; no remote branch/commit/PR.  
**Migration:** `c1d4e7a9f204_guardian_private_evidence_and_cases.py`.

## Added files

| Path | Purpose |
|---|---|
| `src/myeconomy/application/guardian.py` | Owner-scoped upload, invoice review, persisted cases, draft and approval application use cases |
| `src/myeconomy/api/guardian_schemas.py` | Strict typed Pydantic input/output contracts |
| `src/myeconomy/api/guardian_routes.py` | Verified-auth Guardian HTTP routes, bounded upload, download and case endpoints |
| `src/myeconomy/infrastructure/document_storage.py` | Local private file adapter with generated keys, restrictive permissions and atomic writes; demo-only |
| `migrations/versions/c1d4e7a9f204_guardian_private_evidence_and_cases.py` | Evidence/case tables, owner composite FK, check constraints, indexes and idempotency constraints |
| `tests/test_guardian_workflow.py` | Upload, replay/conflict, ownership, persistence, audit, abstention, draft/approval, explicit-false rejection and prior-bill anomaly tests |
| `demo_data/synthetic_v1/source_documents/guardian/guardian_previous_bill.pdf` | Fictional INR 800 prior-period invoice |
| `demo_data/synthetic_v1/source_documents/guardian/guardian_current_bill_anomaly.pdf` | Fictional INR 1,180 later-period bill with an unusual increase |
| `demo_data/synthetic_v1/source_documents/guardian/guardian_arithmetic_mismatch.pdf` | Fictional invoice with line arithmetic discrepancy |
| `demo_data/synthetic_v1/api_scenarios/07_guardian_document_review_workflow.json` | API-oriented scenario metadata for the Guardian document journey |
| `demo_data/synthetic_v1/guardian_workflow/invoice_payloads.json` | Structured synthetic invoice request examples and verified locators |
| `demo_data/synthetic_v1/guardian_workflow/run_demo.py` | Local API demo runner; uploads documents, submits review and creates drafts only |
| `demo_data/synthetic_v1/guardian_workflow/README.md` | Demo prerequisites, steps and limitations |
| `demo_data/synthetic_v1/metadata/guardian_workflow_manifest.json` | SHA-256/size manifest for three Guardian PDF fixtures |
| `docs/iterations/ITERATION-04.md` | Scope, invariants, APIs, tests, limitations and next acceptance gates |
| `docs/iterations/ITERATION-04-FILE-MANIFEST.md` | This manifest |

## Modified files

| Path | Change |
|---|---|
| `.gitignore` | Ignore `.data/` and local private document storage |
| `.env.example` | Add `AWNNORA_DOCUMENT_ROOT` local/demo setting |
| `PUSH_TO_GITHUB.md` | Replace obsolete Iteration 03 push instructions with verified Iteration 04 branch/apply/test guide |
| `src/myeconomy/infrastructure/models.py` | Add `GuardianEvidenceDocument` and `GuardianCase` ORM models |
| `src/myeconomy/main.py` | Register Guardian router; identify application as AwnNORA API v0.4.0 |
| `tests/conftest.py` | Add migration head and per-test temporary private document root |
| `src/myeconomy/api/guardian_routes.py` | Add download-access audit event and commit after successful owner-only blob retrieval |
| `docs/PROJECT_STATUS.md` | Record remote PR #3 and local Iteration 04 accurately |
| `docs/AWNNORA_CONTEXT_MAP.md` | Update remote/local state and Guardian API trust boundary |
| `docs/PROJECT_MEMORY.md` | Reconcile Iterations 03–04 and runtime limitations |
| `docs/FEATURE_CATALOG.md` | Mark Guardian capability partial with exact boundaries |
| `docs/CODEBASE_MAP.md` | Add Guardian application/API/storage/model/migration/runtime paths |
| `docs/ARCHITECTURE.md` | Add the current Guardian API architecture and storage boundary |
| `docs/THREAT_MODEL.md` | Add Guardian upload, evidence spoofing, local-storage, orphan-blob and download threat analysis |
| `docs/TURBO_PARALLEL_ENGINEERING.md` | Rebase workstream order and state on merged PR #3 + local Iteration 04 |
| `docs/iterations/ITERATION-03.md` | Mark Iteration 03 merged via PR #3 |
| `README.md` | Update implementation ledger, Guardian endpoints and demo instructions |
| `demo_data/synthetic_v1/README.md` | Document Guardian synthetic add-on |
| `docs/DEMO_PLAYBOOK.md` | Add executable Guardian API workflow steps |

## Deliberately not changed

- No `.env`, bearer token, password, live user record, local database file or private document is part of this manifest.
- No existing `main` branch file has been changed remotely.
- Existing 42-table / 17,425-row core dataset is unchanged; Guardian workflow PDFs and payloads are an additive demo supplement.
