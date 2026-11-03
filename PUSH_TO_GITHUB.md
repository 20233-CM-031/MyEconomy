# Push the complete MyEconomy project and synthetic demo corpus

Repository: `20233-CM-031/MyEconomy`  
Suggested branch: `iteration/01-trust-and-synthetic-demo-data`

## What this package contains

- Iteration 00 deterministic cashflow API foundation.
- Iteration 01 identity, email verification, sessions, household invitations and explicit consent.
- Durable product memory, architecture, codebase map, feature catalog, threat model, iteration records and hackathon scorecard.
- `demo_data/synthetic_v1/`: 42 entity tables, 17,425 synthetic records, CSV/JSON/JSONL/PostgreSQL SQL/SQLite, synthetic invoice HTML/PDF/PNG, scenarios, business rules, regulatory engineering notes, validators and reproducible scripts.

All data in `demo_data/synthetic_v1/` is fictional. Keep the `SYNTHETIC DEMO` label visible. Do not connect fixtures to real banks, payment rails, providers, government portals, insurers or customers.

## Windows PowerShell upload procedure

1. Download `MyEconomy_Complete_Project_Demo_v1.zip` and extract it. The ZIP contains a top-level `MyEconomy` directory.
2. Clone the repository and create a feature branch from the latest remote main:

```powershell
git clone https://github.com/20233-CM-031/MyEconomy.git
cd MyEconomy
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c iteration/01-trust-and-synthetic-demo-data
```

3. Set `$source` to the extracted `MyEconomy` folder, then overlay its files. Do not use `/MIR`; preserve `.git` and existing local work. The synthetic SQLite file is intentionally included and must not be excluded.

```powershell
$source = "C:\path\to\extracted\MyEconomy"
$destination = (Get-Location).Path
robocopy $source $destination /E `
  /XD .git .venv .pytest_cache .ruff_cache __pycache__ `
  /XF .env *.pyc *.pyo
```

4. Review the working tree before running anything:

```powershell
git status --short --branch
git diff --check
git diff --stat
```

5. Install and validate:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
python -m compileall -q src tests migrations scripts
python demo_data\synthetic_v1\validate_dataset.py demo_data\synthetic_v1
```

6. Commit and push:

```powershell
git add -A
git diff --cached --check
git diff --cached --stat
git commit -m "feat: add trust foundation and synthetic economic demo corpus"
git push -u origin iteration/01-trust-and-synthetic-demo-data
```

7. Open a Pull Request into `main`. Review the diff and wait for CI. Never force-push. If remote files changed after this archive was prepared, reconcile the changes rather than overwriting them.

## Dataset-only option

`MyEconomy_Synthetic_Demo_Dataset_v1.zip` contains a top-level `synthetic_v1` directory. Copy it to `MyEconomy/demo_data/synthetic_v1/` in a separate branch only after comparing the existing dataset manifest.

## Limits

The GitHub connector used during preparation could read the repository but branch creation and remote writes returned HTTP 403. This package is therefore a local delivery; it has not been pushed by the assistant. The verified SQLite database is for synthetic local demos. PostgreSQL seed/schema are provided but have not been executed against a live PostgreSQL server. Real SMTP and financial-provider integrations remain outside this delivery.
