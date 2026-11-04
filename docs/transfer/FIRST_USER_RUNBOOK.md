# AwnNORA — First User Local Journey

This runbook demonstrates one person's Personal Mode without a live bank connection, Commons membership, or real provider integration. Use a dedicated local account and fictional persona only.

## 1. Prepare the local environment

Requirements: Python 3.12 or 3.13, a local SQLite database (or a PostgreSQL development instance), and the repository's installed development dependencies.

PowerShell, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set these local-only values in `.env` (the repository's `.env.example` uses the same variable names):

```dotenv
APP_ENV=development
EMAIL_BACKEND=log
DATABASE_URL=sqlite:///./myeconomy.db
```

The development-only log email adapter prints the one-time verification token to the API console. This is strictly for local use and must never be enabled in production.

Apply migrations and start the server:

```powershell
alembic upgrade head
uvicorn myeconomy.main:app --reload
```

Check `http://127.0.0.1:8000/health/ready` and open `/docs`.

## 2. Create a dedicated demo user

Use a non-deliverable `@example.invalid` email such as `awnnora-demo-01@example.invalid`. Choose a password of at least 12 characters. Do not use a real customer's credentials.

```powershell
python scripts/awnnora_first_user_journey.py --email "awnnora-demo-01@example.invalid" --register
```

The script prompts for the password and for the one-time verification token printed by the development mail adapter. It does not save the password or session token.

For an already-created, verified local demo account, omit `--register`.

## 3. What the journey does

1. Authenticates the user and verifies email state.
2. Loads `CUS00001` (or another selected persona) into that existing account using `scripts/seed_synthetic_customer.py`.
3. Persists synthetic financial accounts, transaction imports and recurring obligations through existing application services.
4. Replays safely on rerun using stable fixture IDs and import idempotency.
5. Reads the user's own accounts and obligations through authenticated routes.
6. Calls `GET /api/v1/personal/power-report` for the October 2026 fixture period.
7. Writes a report under `demo_output/first_user/first_user_report.json`.

Default fixture period is 1–31 October 2026, with an as-of date of 4 November 2026. Override dates explicitly when testing a different imported period.

## 4. Optional Guardian add-on

```powershell
python scripts/awnnora_first_user_journey.py --email "awnnora-demo-01@example.invalid" --include-guardian-manual-demo
```

This optional mode uploads three fictional PDFs and submits manually prepared structured invoice fields. It does **not** perform OCR, malware scanning, Meta model extraction, locator verification, provider contact or payment. The existing Guardian status remains `STORED_UNSCANNED`; do not use this optional path as proof that a document trust pipeline is production-ready.

## 5. Expected product truth

- Personal Power Report is read-only.
- The report uses imported records, not a verified bank balance.
- Potential duplicate and due-date findings require human checking.
- A possible saving is not a saving; a submitted request is not a recovery; an eligibility match is not an award.
- Synthetic demo VIVC must remain zero.
- The user can use Personal Mode without joining Commons.
- No real bank, merchant, employer, insurer, government or payment provider is contacted.

## 6. Reset / repeat

The seed loader is idempotent. Re-run the journey to demonstrate replay without duplicating the same synthetic import. For a clean demo, use a fresh local database and a new dedicated local user. Do not delete or manipulate production data to reset a demonstration.
