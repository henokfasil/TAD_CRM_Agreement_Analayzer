# CODEX Session Start

This project is the **CRM Agreement Intelligence System** described in `Master Prompt.txt`.

## Current State

Phase 1 foundation has been scaffolded in this folder. The repository was initially empty except for:

- `Master Prompt.txt`
- `CRM Agreements.pdf`

The master prompt has mojibake/encoding artifacts in some punctuation, but its requirements are readable.
`CRM Agreements.pdf` was smoke-tested with the PDF parser: PyMuPDF extracted 53 pages and page 1 text.

Streamlit Community Cloud deploys from GitHub using `requirements.txt`. Do not commit `uv.lock` from
the OECD Windows environment because it can capture internal Nexus package URLs that Streamlit Cloud
cannot resolve.

Streamlit pages add the repository root directly to `sys.path` using `Path(__file__).resolve()`
before importing backend code. This is needed because Streamlit Cloud launches `streamlit_app/Home.py`
and may otherwise fail with import errors such as `ModuleNotFoundError: No module named 'app'` or
`No module named 'streamlit_app'`.

The app is deployed on Streamlit Community Cloud at:

```text
https://crmagreement.streamlit.app
```

The cloud deployment currently shows the Phase 1 shell and codebook count. The local PDF is not
included in GitHub because `*.pdf` is ignored; cloud users should use the upload tab for documents.

Phase 1B adds a Streamlit session document workspace:

- `New Document Ingestion` registers extracted PDFs in `st.session_state.document_workspace`;
- `Agreement Explorer` can browse extracted documents and page-level text from that session;
- workspace data can be downloaded as JSON or page-level CSV;
- this is session-scoped and ephemeral on Streamlit Cloud until a real database is attached.

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
- Streamlit ingestion page can upload a PDF or extract the local `CRM Agreements.pdf`, display hash,
  duplicate status, parser metadata, page count, and page-level extracted text.
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

After adding the Streamlit import-path guard, the test suite result is `5 passed`.

After adding the session document workspace, the test suite result is `6 passed`.

`python -m compileall app streamlit_app tests` can fail locally in the OneDrive folder with
`PermissionError` while writing `__pycache__` files. Treat pytest as the reliable validation signal
in this workspace unless the project is moved to a normal local filesystem.

Smoke commands:

```powershell
uv run python scripts/seed_codebook.py
```

Result: `Loaded 88 variables from v1.`

Streamlit visible ingestion smoke:

```powershell
uv run python -c "from pathlib import Path; from app.services.parsing.pdf import extract_pdf_pages; r=extract_pdf_pages(Path('CRM Agreements.pdf')); print(len(r.pages))"
```

Result: `53`.

Streamlit on this Windows setup should be launched from the project folder with `python -m streamlit`
rather than the direct `streamlit` console script:

```powershell
cd "C:\Users\telila_h\OneDrive - OECD\OECD files\CRM_Agreements"
$env:UV_CACHE_DIR = Join-Path $env:TEMP 'crm-uv-cache'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'crm-agreement-intelligence-venv'
uv run python -m streamlit run streamlit_app/Home.py
```
