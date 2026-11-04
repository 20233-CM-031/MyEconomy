# Iteration 04 — Guardian Evidence & Invoice Review API Vertical

**Date:** 2026-11-04  
**Status:** Local candidate integrated and tested; not pushed or merged.  
**Verified remote base:** `main` at `5b5cf669773d5c0cd33f5abffb8c46d44cead797` (PR #3 merge).  
**Migration:** `c1d4e7a9f204` (`f2e9c7a4d821` parent).  
**Primary architecture roles:** Guardian (user-facing capability), MAKOS (workflow surface/API), GENIEA (policy boundary for future execution), KRN (evidence/provenance contract for future knowledge links).

## 1. Problem

The Iteration 03 kernel could evaluate structured invoice data but did not provide a user-accessible route to store evidence, persist review cases or prepare a safe next action. This iteration turns that domain logic into a bounded authenticated API workflow while keeping extraction and external actions outside the trust boundary.

## 2. User journey and scope

1. A verified user uploads a PDF, PNG or JPEG evidence file.
2. The API bounds request size, checks declared MIME and file signature, sanitizes the display filename, hashes the original bytes and uses owner-scoped idempotency.
3. A private local filesystem adapter writes a generated UUID blob path with restrictive permissions and atomic rename; database metadata and audit event commit together.
4. The user submits structured invoice values and evidence locator strings.
5. The application checks ownership, request idempotency and prior invoices belonging to the same user/provider/currency, then calls deterministic `review_invoice(...)`.
6. The service persists an owner-scoped case, input snapshot, finding snapshot and audit event in one transaction.
7. The user can inspect the case, generate a clarification draft and explicitly approve it for manual sending.

## 3. Implemented invariants

- Every upload and case belongs to one user. The case's composite foreign key binds `evidence_document_id` and `owner_user_id` to the same evidence row.
- All routes require verified authentication. A household member cannot access the owner's file/case by virtue of membership.
- Upload maximum is 5 MiB and allowed declared types are PDF, PNG and JPEG. Magic signatures must match declared MIME.
- Original filenames never become storage paths. Generated owner/document UUIDs form the local storage key.
- SHA-256 and owner-scoped idempotency are stored. Repeating the same key with identical bytes/payload replays the existing object/case; reusing it with changed data conflicts.
- Case input, review outcome and audit event share a database transaction. Unique-key races can happen during flush and are handled as replay/conflict outcomes.
- Prior invoice comparisons are owner-specific and restricted to the same normalized provider key and currency.
- No model-generated arithmetic, eligibility or authorization is authoritative. The review kernel uses exact Decimal/currency precision.
- A draft is not a submission. Approval only records `APPROVED_FOR_USER_TO_SEND`; no external side effect is executed.
- Uploaded files remain `STORED_UNSCANNED`. The code does not pretend a file is safe or extracted.

## 4. API contracts

- `POST /api/v1/guardian/evidence-documents` — raw upload body; headers `Content-Type`, `Idempotency-Key`, `X-Filename`.
- `GET /api/v1/guardian/evidence-documents` — owner metadata list.
- `GET /api/v1/guardian/evidence-documents/{document_id}/download` — owner-only download.
- `POST /api/v1/guardian/invoice-reviews` — structured invoice request; `Idempotency-Key` required.
- `GET /api/v1/guardian/cases` and `GET /api/v1/guardian/cases/{case_id}` — owner-scoped case reads.
- `POST /api/v1/guardian/cases/{case_id}/draft` — create a clarification draft.
- `POST /api/v1/guardian/cases/{case_id}/approve-draft` — JSON `{"confirm": true}` required; records manual-send approval only.

## 5. Storage and trust boundary

`LocalPrivateDocumentStore` uses a configurable `AWNNORA_DOCUMENT_ROOT`, generated UUID paths, directory mode `0700`, file mode `0600`, `fsync` and atomic rename. This is an isolated development/demo adapter, not production-grade encrypted storage. POSIX permissions are not encryption. Deployments with real financial documents require encrypted object storage, KMS-managed keys, scanner/quarantine workflow, retention/deletion policies, backup/restore validation, malware/content inspection, access logging and incident procedures.

The file content is not parsed, executed or passed to an LLM. Client-supplied evidence locator strings are persisted but not checked against PDF text/page regions. Invoice fields and extraction-confidence values are supplied by the caller. Therefore this iteration is a structured-input review API, not AI/OCR extraction and not verified evidence matching.

## 6. Synthetic demonstration

`demo_data/synthetic_v1/guardian_workflow/` supplies three fictional bill scenarios:

- prior INR 800 broadband bill (baseline);
- current INR 1,180 bill (same plan, unusual increase requiring review, not proof of impropriety);
- installation bill with a deliberate line arithmetic discrepancy.

The PDFs identify themselves as synthetic. `invoice_payloads.json` contains manually prepared structured fields and locators. `metadata/guardian_workflow_manifest.json` lists byte size and SHA-256 for each PDF. Locators were checked against `pdftotext -layout` output for the exact files.

Run from repository root after applying migrations, starting the local API and obtaining a verified local bearer token:

```bash
AWNNORA_DEMO_BEARER_TOKEN="<local-demo-user-token>" python demo_data/synthetic_v1/guardian_workflow/run_demo.py
```

PowerShell:

```powershell
$env:AWNNORA_DEMO_BEARER_TOKEN = "<local-demo-user-token>"
python demo_data/synthetic_v1/guardian_workflow/run_demo.py
```

The script creates drafts for review findings and stops. It does not approve drafts or contact any provider.

## 7. Files added or modified

See `docs/iterations/ITERATION-04-FILE-MANIFEST.md` for exact paths and purposes.

## 8. Verification

- `PYTHONPATH=src pytest -q`: **84 passed**.
- `python -m compileall -q src tests migrations scripts demo_data/synthetic_v1`: passed.
- SQLite `upgrade head -> downgrade base -> upgrade head`: passed; `c1d4e7a9f204` is head.
- `PYTHONPATH=src python demo_data/synthetic_v1/validate_dataset.py`: passed all existing dataset checks across 42 tables / 17,425 rows.
- Guardian PDF text/locator inspection via `pdftotext -layout`: completed; separate SHA-256 manifest generated.
- Python 3.13 used. Python 3.12 unavailable in this environment.
- Ruff unavailable; lint/format not verified.
- New migration not run against live PostgreSQL 16 in this environment.
- Standalone demo script compile-checked; not executed against a separately started local server in this environment.

## 9. Known gaps / next acceptance gates

1. Implement scanner state machine: `STORED_UNSCANNED -> SCANNING -> CLEAN|REJECTED`, with failure/retry quarantine, provider-independent scanning adapter and security tests.
2. Replace local filesystem adapter for deployment with encrypted object storage/KMS and retention/erasure/backup/restore controls.
3. Add model gateway for document classification and schema-constrained extraction. Every output must include model, schema/prompt version, exact page/region locator and calibrated confidence; unknown/weak fields must abstain.
4. Verify locators against original document rendering/text and preserve source spans; extracted evidence cannot just be user-asserted.
5. Add PostgreSQL 16 migration/service tests, upload concurrency tests, DB/file orphan reconciliation and compensating cleanup for crash windows.
6. Add a durable GENIEA case mission/checkpoint/outbox and step-level idempotency/approval lifecycle.
7. Expose this workflow in MAKOS with progress, evidence preview, findings, confidence, draft and approval history.
8. Add a KRN provenance/evidence graph adapter with private partition and temporal validity before sharing selected graph edges.
9. Add real provider delivery only with verified endpoint/identity, contract, explicit approval, idempotency, retry, reconciliation and dispute route.

## 10. Remote status

No Iteration 04 remote change has been made. GitHub confirmed PR #3 and current `main` SHA above. The currently available GitHub App installation still belongs to `kareem1207`; it excludes the repository owned by `20233-CM-031`. Creating the Iteration 04 branch returned HTTP 403. Use a reviewed feature branch from current `origin/main`; never apply this candidate directly to `main`.
