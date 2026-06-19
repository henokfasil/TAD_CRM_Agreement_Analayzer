# CODEX Session Start

This project is the **CRM Agreement Intelligence System** described in `Master Prompt.txt`.

## Current State

Phase 1 foundation has been scaffolded in this folder. The repository was initially empty except for:

- `Master Prompt.txt`
- `CRM Agreements.pdf`

The master prompt has mojibake/encoding artifacts in some punctuation, but its requirements are readable.
`CRM Agreements.pdf` was smoke-tested with the PDF parser: PyMuPDF extracted 53 pages and page 1 text.

Git is initialized locally using a separate metadata directory outside OneDrive:

```text
C:/Users/telila_h/AppData/Local/GitRepos/CRM_Agreements.git
```

The working tree remains in the OneDrive folder, but `.git` is only a pointer file. This avoids the
OneDrive lock-file problem that broke normal `git init`.

## Phase 1 Scope Implemented

- Python project metadata in `pyproject.toml`.
- FastAPI app in `app/main.py`.
- Settings loader in `app/core/config.py`.
- SQLAlchemy models in `app/db/models/`.
- Alembic migration in `alembic/versions/0001_phase1_foundation.py`.
- YAML codebook in `config/codebooks/crm_codebook_v1.yaml`.
- Active codebook pointer copy in `config/codebooks/active_codebook.yaml`.
- Codebook loader in `app/services/codebook.py`.
- Local document storage and SHA-256 duplicate detection in `app/services/ingestion/storage.py`.
- PDF extraction with page preservation in `app/services/parsing/pdf.py`.
- Basic API routes under `app/api/routes/`.
- Starter Streamlit app under `streamlit_app/`.
- Phase 1 tests under `tests/`.

## Important Design Rule

Do not present AI-generated legal coding as validated fact. Keep raw AI outputs, verifier outputs,
review decisions, adjudication decisions, and final validated decisions distinct in both schema and UI.

## Session Handoff Rule

Always update this `CODEX.md` file whenever meaningful project state changes, including:

- new architecture or implementation decisions;
- completed phases or milestones;
- commands that were run and their results;
- known blockers, environment quirks, or workarounds;
- Git/GitHub setup changes;
- next recommended steps.

Treat this file as the first thing a future Codex session should read before continuing work.

## Next Recommended Work

1. Run `uv sync --extra dev` if dependencies are not installed.
2. Run `uv run pytest`.
3. Initialize Git if desired.
4. Configure PostgreSQL and run Alembic migrations.
5. Continue Phase 1 hardening before starting Phase 2:
   - Replace in-memory API repositories with database-backed repositories.
   - Add integration tests for file upload.
   - Add a small fixture PDF or generated test PDF.
   - Add Streamlit API client layer instead of direct placeholders.

## Commands Intended

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app/Home.py
```

## Last Verification

Because Python was not available through the plain `python` or `py` launchers, tests were run through
`uv`. On this Windows/OneDrive environment, `uv` needed cache and virtual-environment paths redirected
to `%TEMP%`.

```powershell
$env:UV_CACHE_DIR = Join-Path $env:TEMP 'crm-uv-cache'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'crm-agreement-intelligence-venv'
uv run --extra dev python -m pytest
```

Result: `4 passed`.

Smoke commands:

```powershell
uv run python scripts/seed_codebook.py
```

Result: `Loaded 88 variables from v1.`
