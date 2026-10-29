# CRM Agreement Intelligence System

A working research prototype for collecting, ingesting, analysing, reviewing, and comparing international critical raw materials agreements. It uses persistent PDF storage, OCR, nine evidence-linked research questions, a configurable codebook, AI-supported analysis, and human review to keep final findings transparent and auditable.

The primary Studio workflow is **Upload → Analyse → Review → Compare**. Detailed provision coding
and verification remain available as advanced methodological controls.

This repository currently provides:

- FastAPI application skeleton.
- SQLAlchemy models and Alembic migration for the core research data model.
- Configurable YAML CRM codebook.
- Local document upload/storage with SHA-256 duplicate detection.
- PDF text extraction with page-level provenance using PyMuPDF.
- Streamlit workflow, dashboard, comparison tools, exports, and an embedded HTML presentation.
- Persistent records in Neon PostgreSQL and original PDFs in Neon Object Storage.
- Automatic nine-question agreement profiles with page-level evidence and human approval.
- A conservative local evidence fallback when an external model is unavailable.
- Tests covering configuration, persistence adapters, analysis, review, hashing, and extraction.

The long-term objective is a research engine that can generate reproducible figures, analysis,
methods and complete reports from the approved live corpus. Monitoring and report automation remain
future work and must not silently claim validated legal conclusions.

## Local Development

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app/Home.py
```

## Optional External LLM API Use

The app defaults to a deterministic mock provider. To use OpenAI for the AI proposal tab, configure
these values in `.env` locally or Streamlit Cloud secrets:

```toml
ALLOW_EXTERNAL_LLM = "true"
OPENAI_API_KEY = "sk-..."
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4.1-mini"
```

To use Gemini instead, configure:

```toml
ALLOW_EXTERNAL_LLM = "true"
GEMINI_API_KEY = "your_key_here"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL = "gemini-3.8-flash"
```

Never commit a real API key or password.
Store all credentials in a local `.env` file or your deployment secret manager, and keep `.env` out of source control.

Gemini requires both a valid key and available project credits. If it is unavailable, the Studio
retains a lower-confidence local evidence scan and clearly labels it for human review.

## Project Guidance

See `AGENTS.md` for the current product contract and `CODEX.md` for the historical implementation
log and continuation context.
