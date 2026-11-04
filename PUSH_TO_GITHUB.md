# Apply and Push — AwnNORA Iteration 03

Repository: `https://github.com/20233-CM-031/MyEconomy`
Product: **AwnNORA**
Verified base: `main` at `a55cb388ef7baf72766e2fcabe89f0dee1c45979` (PR #2 merged).
Suggested branch: `iteration/03-guardian-evidence-kernel`.

## 1. Start from the current remote base

```powershell
git clone https://github.com/20233-CM-031/MyEconomy.git
cd MyEconomy
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c iteration/03-guardian-evidence-kernel
```

Verify that `git rev-parse HEAD` matches the current remote `main` before applying this overlay. If `main` has advanced, use the latest `origin/main` and rerun the entire test suite.

## 2. Apply the overlay

Extract `AwnNORA_Iteration_03_Overlay.zip` into the repository root, preserving paths and allowing the listed files to be replaced. The overlay contains only Iteration 03 additions/updates; it is not a replacement for the complete project.

Alternatively, copy the individual files from the download package to their exact repository-relative paths. Do not copy local databases, `.env` files, caches or Python bytecode.

## 3. Validate

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
pytest -q
ruff check src tests migrations scripts
ruff format --check src tests migrations scripts
python -m compileall -q src tests migrations scripts
python demo_data/synthetic_v1/validate_dataset.py
git diff --check
git status --short
```

Expected local test total for this source snapshot: **79 passed**. Also run the CI matrix on Python 3.12, Python 3.13 and PostgreSQL 16. Ruff is not installed in the assistant's isolated environment, so do not treat Ruff as passed until you run it. PostgreSQL should be rerun on the feature branch even though Iteration 02's migration passed its merged CI.

## 4. Inspect and push

```powershell
git add AGENTS.md README.md PUSH_TO_GITHUB.md src/myeconomy/domain/economic_intelligence.py tests/test_economic_intelligence.py docs
git commit -m "feat: add AwnNORA economic intelligence kernel"
git push -u origin iteration/03-guardian-evidence-kernel
```

Open a Pull Request into `main`. Review the domain/API boundary carefully: Iteration 03 is currently a pure domain kernel and its rules are not yet wired to authenticated routes, storage, Meta model extraction or MAKOS UI. Do not merge based on test count alone.

## 5. GitHub connection issue (assistant-side)

The assistant's GitHub connection currently authenticates as `20233-CM-031`, but the GitHub App installation is attached to `kareem1207` and its visible repository list excludes `20233-CM-031/MyEconomy`. Branch creation returned HTTP 403 `Resource not accessible by integration`. This guide uses the user's own authenticated Git client; no personal access token should be pasted into chat.

## 6. Safety

- Never commit `.env`, credentials, live financial records, local database files or private document contents.
- Keep all sample users/records labelled synthetic.
- Personal information is private by default; Commons requires separate purpose-specific consent.
- An invoice finding is not proof of fraud or legal violation. A proposed action is not submitted until a real integration and explicit approval exist.
- VIVC excludes synthetic, estimated, attempted and unverified value.
