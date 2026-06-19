# CRM Agreement Intelligence System

Phase 1 foundation for a semi-autonomous, human-in-the-loop research platform for
international critical raw materials agreements.

This repository currently provides:

- FastAPI application skeleton.
- SQLAlchemy models and Alembic migration for the core research data model.
- Configurable YAML CRM codebook.
- Local document upload/storage with SHA-256 duplicate detection.
- PDF text extraction with page-level provenance using PyMuPDF.
- Starter Streamlit pages for dashboard, ingestion, agreement browsing, review, and codebook admin.
- Tests for configuration, codebook loading, hashing, and text extraction behavior.

The later LLM coding, verification, discovery, adjudication, analytics, and monitoring systems are
represented as explicit typed stubs. They should be implemented in later phases without silently
claiming validated legal coding.

## Local Development

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn app.main:app --reload
uv run streamlit run streamlit_app/Home.py
```

## Phase Discipline

See `CODEX.md` for the current implementation state and continuation instructions.

