# AwnNORA MAKOS Web + Meta Assistance — Local Runbook

This runbook describes the local overlay in this delivery package. Apply the overlay only to a clean checkout of the verified merged Iteration 05 baseline.

## 1. Apply locally

From the extracted delivery directory:

```powershell
python .\apply_overlay.py --target "C:\path\to\MyEconomy" --dry-run
python .\apply_overlay.py --target "C:\path\to\MyEconomy"
```

The script patches shared files only when expected source anchors are present, refuses conflicting new paths, and performs no Git operation. Review the file manifest before running it against your working checkout.

## 2. Start the Python API

Use Python 3.12 or 3.13:

```powershell
cd C:\path\to\MyEconomy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Use local-only `.env` settings:

```dotenv
APP_ENV=development
EMAIL_BACKEND=log
DATABASE_URL=sqlite:///./myeconomy.db
```

Apply the new consent migration and start the API:

```powershell
alembic upgrade head
uvicorn myeconomy.main:app --reload
```

Check `http://127.0.0.1:8000/health/ready`.

## 3. Create and seed the first local user

The MAKOS UI now supports account registration, email verification and sign-in. For the synthetic first-user journey, use a dedicated non-deliverable `@example.invalid` address. The development log mail adapter prints the one-time verification token in the API console. The page's as-of date follows the browser's local date; the October 2026 sample scenario is not a permanent production date.

Register from the web UI, copy the one-time verification token from the API console, and enter it in the verification step. Then seed the synthetic persona into that existing verified user from a second PowerShell terminal:

```powershell
$env:APP_ENV = "demo"
python scripts/seed_synthetic_customer.py --user-email "awnnora-demo-01@example.invalid" --customer-id CUS00001
```

Do not use any real customer's email, password, statement or bearer token. The persona and imported financial facts are synthetic fixtures. Seeding is idempotent.

You can also run the full first-user API journey from the repository root when you prefer the scripted route:

```powershell
$env:APP_ENV = "development"
python scripts/awnnora_first_user_journey.py --email "awnnora-demo-01@example.invalid" --register
```

The scripted runner verifies the account, seeds the persona, and writes `demo_output/first_user/first_user_report.json`. When you use the script, the browser can sign into that same user.

## 4. Start the TypeScript MAKOS web client

Requirements: Node.js 20.19+ or 22.12+ and npm. From a new PowerShell terminal:

```powershell
cd C:\path\to\MyEconomy\apps\web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite development server proxies `/api/*` and `/health/*` to `http://127.0.0.1:8000`. Override `AWNNORA_API_PROXY_TARGET` in a local `.env` file under `apps/web` only when the API runs elsewhere. Do not place server secrets in any `VITE_*` variable.

The default screen is an explicitly labelled synthetic demonstration. Select **Connect account**, sign in with the verified local demo user, and the workspace switches to private-account mode. The report then comes from the authenticated Python API. From the overview, create an INR account and upload a statement you are authorized to use. The UI enforces a 2 MiB client-side size limit, uses a SHA-256-derived idempotency key, and refreshes the report after the import commits. If report refresh fails, it tells you the import was already saved and not to upload the same file again. The bearer token is kept in browser memory only; a page reload requires another sign-in.

## 5. Enable Muse Spark 1.3 Standard-mode assistance

The Meta Model API key is server-side only. Add it to the repository root `.env`:

```dotenv
MODEL_API_KEY=your-meta-model-api-key
```

Restart the API. Never put this value in `apps/web/.env`, source code, an HTML page, browser storage or a client-side environment variable.

In MAKOS, open **AI intelligence**. Read the separate AI assistance consent and select the checkbox to grant it. The grant is restricted to:

- Purpose: `ai_assistance`
- Categories: `financial_summary` and `household_obligations` (both are required because the report explanation includes an aggregate of upcoming essential obligations)
- Recipient type: `service`
- Recipient ID: `meta-model-api`
- Terms version: `2026-11-04.1`

Only after the consent is active can the user submit a question. The endpoint calls `muse-spark-1.3` in Standard mode, sets `store=false`, sends no tools, and requests strict JSON-schema output. The server creates the prompt from the authenticated user's aggregate-only report; the browser cannot submit arbitrary prompt text. Payee names and evidence locators are omitted, and recurring-obligation titles are genericized before the request. The adapter rejects unknown finding IDs, malformed output and missing credentials. It does not create or mutate a case, send a provider message, calculate money, approve a claim or settle a value event.

The consent can be revoked in the same AI intelligence workspace. Revocation blocks future calls; it cannot recall a request already transmitted to Meta. The Model API adapter does not store the prompt in AwnNORA's database or audit log.

## 6. Test and quality gates

From the repository root:

```powershell
ruff check src tests migrations
ruff format --check src tests migrations
PYTHONPATH=src pytest -q
python -m compileall -q src tests migrations scripts
alembic downgrade base
alembic upgrade head
```

Validate the existing and supplemental synthetic corpora:

```powershell
python demo_data/synthetic_v1/validate_dataset.py
python tools/awnnora_scenario_lab/validate.py demo_data/scenario_lab_v1
```

For the web client:

```powershell
cd apps/web
npm run typecheck
npm run build
```

Before production, also run PostgreSQL 16 migration and service tests, dependency scanning, frontend accessibility and browser tests, load tests, backup/restore and consent-revocation concurrency tests. The local SQLite demo is not a production-readiness certification.

## 7. Honest demo boundaries

- The existing synthetic corpus and all demo-screen values are fictional.
- Personal Power Report is a read-only analysis of imported records, not a verified bank balance.
- Potential duplicate findings are not confirmed double charges or recovered money.
- Existing Guardian documents remain `STORED_UNSCANNED`; OCR/model extraction is not active.
- Opportunity, Entitlement, Resource Exchange, Crisis Shield and Commons screens are illustrative synthetic previews, not connected live exchanges or official schemes.
- The enterprise price calculator runs locally with integer-paise arithmetic, but does not create a posted order or financial record.
- Muse Spark is a real provider call only when the user is authenticated, has consented, the server key is configured and the request succeeds. No key or failure means no model result; do not substitute a fixture response and claim that Meta was used.
- Voice transcription, SAM 3.1, Muse Glimmer and Muse Image are named as integration targets, not live integrations in this package.
- No payment, refund, claim, job, benefit award, provider negotiation, external email or payout is performed.
- Synthetic value events never count as live VIVC.

## 8. Production release blockers

Do not use real financial documents or real customer personal data until the deployment has encrypted object storage and KMS, malware scanning/quarantine, sandboxed parsing, verified evidence locators, purpose/recipient-bound consent at every reader, robust login abuse controls and account recovery, MFA/passkeys, TLS/secrets management, retention/export/erasure, PostgreSQL concurrency tests, backups/restore, operational telemetry, incident response and independent security/privacy/legal review. The current repository's local Guardian storage adapter is not production-safe for financial documents.


The optional Meta consent covers `financial_summary` and `household_obligations` only. Both categories are required because the explanation request includes an aggregate essential-obligation total. The endpoint sends no payee names; recurring-obligation titles are genericized before leaving the service. Requests use one of four fixed intents and are limited to a 365-day period.
