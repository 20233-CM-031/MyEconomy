# Apply and Push — AwnNORA Iteration 04

Repository: `https://github.com/20233-CM-031/MyEconomy`
Product: **AwnNORA** (implementation repository/package remains `MyEconomy`).
Last verified `main` base on 2026-11-04: `5b5cf669773d5c0cd33f5abffb8c46d44cead797` (PR #3 merged).
Suggested branch: `iteration/04-guardian-document-workflow`.

## 1. Start from fresh remote main

```powershell
git clone https://github.com/20233-CM-031/MyEconomy.git
cd MyEconomy
git fetch origin
git switch main
git pull --ff-only origin main
git rev-parse HEAD
```

The final command must be compared with the latest `origin/main`. The SHA above is the last SHA checked during preparation; if `main` has advanced, branch from the latest `origin/main`, inspect conflicts and rerun all checks. Do not reset or force-push.

```powershell
git switch -c iteration/04-guardian-document-workflow
```

## 2. Apply the Iteration 04 overlay

Extract `AwnNORA_Iteration_04_Overlay.zip` into the repository root, preserving folder paths and allowing the listed files to be added/replaced. Or copy the individual files at the exact paths shown in `docs/iterations/ITERATION-04-FILE-MANIFEST.md`.

Do not copy `.env`, a local database, `.data/`, private customer evidence, cache directories or bytecode. The ZIP overlay intentionally excludes them.

## 3. Validate locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
pytest -q
ruff check src tests migrations scripts
ruff format --check src tests migrations scripts
python -m compileall -q src tests migrations scripts demo_data/synthetic_v1
python demo_data/synthetic_v1/validate_dataset.py
git diff --check
```

Expected test result for this prepared candidate: **84 passed**. The assistant locally verified Python 3.13, SQLite migration lifecycle and dataset validation. Python 3.12 and Ruff were unavailable. Run the CI matrix on Python 3.12, Python 3.13 and PostgreSQL 16 before merging. A PostgreSQL offline SQL generation check was performed, but it is not a live PostgreSQL 16 migration test.

## 4. Inspect, commit and push

```powershell
git status --short
git diff --stat
git diff --check
```

Review the complete diff, especially `guardian_routes.py`, `guardian.py`, the model, migration and `.env.example`. Then stage the exact paths listed in the manifest. A safer approach after confirming the worktree contains only this change is:

```powershell
git add .gitignore .env.example README.md PUSH_TO_GITHUB.md `
  src/myeconomy/api/guardian_routes.py `
  src/myeconomy/api/guardian_schemas.py `
  src/myeconomy/application/guardian.py `
  src/myeconomy/infrastructure/document_storage.py `
  src/myeconomy/infrastructure/models.py `
  src/myeconomy/main.py `
  migrations/versions/c1d4e7a9f204_guardian_private_evidence_and_cases.py `
  tests/conftest.py tests/test_guardian_workflow.py `
  demo_data/synthetic_v1/guardian_workflow `
  demo_data/synthetic_v1/source_documents/guardian `
  demo_data/synthetic_v1/metadata/guardian_workflow_manifest.json `
  demo_data/synthetic_v1/README.md `
  docs/ARCHITECTURE.md docs/AWNNORA_CONTEXT_MAP.md docs/CODEBASE_MAP.md `
  docs/DEMO_PLAYBOOK.md docs/FEATURE_CATALOG.md docs/PROJECT_MEMORY.md `
  docs/PROJECT_STATUS.md docs/TURBO_PARALLEL_ENGINEERING.md `
  docs/iterations/ITERATION-03.md `
  docs/iterations/ITERATION-04.md docs/iterations/ITERATION-04-FILE-MANIFEST.md

git diff --cached --check
git commit -m "feat: add AwnNORA Guardian evidence review workflow"
git push -u origin iteration/04-guardian-document-workflow
```

Open a PR to `main`. Require the CI matrix, review migration rollback, verify authorization/concurrency behavior and inspect the local storage limitations before merge.

## 5. Important capability boundaries

- Uploaded evidence remains `STORED_UNSCANNED`; the local filesystem adapter is for development/demo, not a production vault.
- The caller supplies structured invoice fields, confidence and locators. No OCR, Meta model extraction, source-locator verification or malware scanner is present.
- The approval endpoint records approval for the user to send manually. It does not send email or contact any provider.
- Synthetic PDFs and fixture values are fictional, and synthetic VIVC is never real impact.

## 6. GitHub connector blocker

Read access works and PR #3 is merged, but the GitHub App installation available to the assistant is attached to `kareem1207`, not the repository owner `20233-CM-031`. The installation's repository list excludes this repository and branch creation returns HTTP 403 `Resource not accessible by integration`. Use your authenticated Git client for this push; do not paste a personal access token into chat.
