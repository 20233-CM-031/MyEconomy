# Guardian Workflow Demo Add-on — AwnNORA Iteration 04

**Environment:** local `development` or isolated `demo` only. **All records and PDFs are fictional.**

This add-on exercises the actual Iteration 04 API with three local PDF files: a prior baseline bill, a later bill with an unusual amount increase, and a bill with an intentional line-arithmetic mismatch. These are not live providers, customers, tax invoices or financial records.

## Prerequisites

1. Install the project and development dependencies: `python -m pip install -e ".[dev]"`.
2. Configure a non-production database and private evidence path in `.env`.
3. Apply migrations: `alembic upgrade head`.
4. Start the API: `uvicorn myeconomy.main:app --reload`.
5. Create and verify a local user through `/api/v1/auth/register` and `/api/v1/auth/verify-email`. With the development log email backend, retrieve the verification token from the application log. Do not use a real customer's data.
6. Set `AWNNORA_DEMO_BEARER_TOKEN` to that local account's bearer token.

## Run the demo

From the repository root:

```bash
python demo_data/synthetic_v1/guardian_workflow/run_demo.py
```

Optional: `AWNNORA_DEMO_BASE_URL=http://127.0.0.1:8000`.

The script uploads the three synthetic PDFs, posts the supplied structured fields, creates a clarification draft for review findings and prints case IDs and dispositions. It deliberately stops before user approval and before any external delivery. The script's input values are in `invoice_payloads.json`.

## API journey

- `POST /api/v1/guardian/evidence-documents` — raw PDF bytes, `Content-Type: application/pdf`, `Idempotency-Key`, `X-Filename`.
- `GET /api/v1/guardian/evidence-documents` — owner-scoped metadata.
- `GET /api/v1/guardian/evidence-documents/{id}/download` — owner-scoped original evidence.
- `POST /api/v1/guardian/invoice-reviews` — structured invoice fields and evidence locators, with its own `Idempotency-Key`.
- `GET /api/v1/guardian/cases` and `GET /api/v1/guardian/cases/{id}` — persisted owner-scoped results.
- `POST /api/v1/guardian/cases/{id}/draft` — deterministic clarification letter, not sent.
- `POST /api/v1/guardian/cases/{id}/approve-draft` — records the user's approval for them to send it; it does not send anything.

## Important implementation boundary

The binary file is stored privately and marked `STORED_UNSCANNED`. The current iteration does not parse PDF/image content, run OCR, call a Meta model, perform malware scanning or contact a provider. The structured values in `invoice_payloads.json` are user-submitted fixture fields. The review kernel then runs exact deterministic arithmetic and owner-specific prior-invoice comparison. Do not label model-assisted extraction as complete.

For production, replace the local filesystem adapter with encrypted object storage + KMS, add malware scanning and retention/deletion lifecycle, and wire a model gateway that returns schema-constrained fields with exact page/region evidence citations. Keep model outputs untrusted and rerun the deterministic validator before any recommendation or action.
