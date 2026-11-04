# Push Iteration 02 — Financial Data Plane v1

Repository: `https://github.com/20233-CM-031/MyEconomy`
Confirmed base: `main` at merged Iteration 01 commit `e25abcffb345fc0a6315114b04c18e8c57a026e6` (2026-11-03).
Suggested branch: `iteration/02-financial-data-plane`.

## 1. Start from the latest main

```powershell
git clone https://github.com/20233-CM-031/MyEconomy.git
cd MyEconomy
git switch -c iteration/02-financial-data-plane
```

Do not branch from the now-merged/stale `iteration/01-trust-and-synthetic-demo-data` branch. PR #1 is already merged into `main`.

## 2. Apply the Iteration 02 overlay

Extract `MyEconomy_Iteration_02_Overlay.zip` into the repository root, preserving directory paths and allowing the listed updated files to be replaced. It contains only Iteration 02 additions/updates, not a replacement copy of the whole repository.

## 3. Validate before committing

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
pytest -q
ruff check src tests scripts
ruff format --check src tests scripts
python -m compileall -q src tests migrations scripts
python demo_data/synthetic_v1/validate_dataset.py
git diff --check
git status --short
```

The expected local pytest result for this delivery is `56 passed`. Ruff was not installed in the isolated build environment; run it on your machine and rely on the branch CI result before merge. The new migration also needs the PostgreSQL 16 CI job to pass.

## 4. Commit and push

```powershell
git add -A
git commit -m "feat: add owner-scoped financial data plane"
git push -u origin iteration/02-financial-data-plane
```

Then open a Pull Request into `main`. Review the code diff, migration, tests, Ruff output and PostgreSQL job before merging. Do not force push.

## 5. Safety

- Never include `.env`, credentials, live financial information or local DB files.
- The dataset is synthetic. Keep `SYNTHETIC_FIXTURE` labels and run the seed script only in `development`, `test` or `demo` environments.
- The synthetic loader requires an existing verified local account and does not create fake login identities.
- The GitHub integration used for assistant-side inspection returned HTTP 403 for branch creation, so the owner must push with an authenticated Git client.
