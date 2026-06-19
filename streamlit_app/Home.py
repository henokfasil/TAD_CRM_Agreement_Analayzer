from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.services.codebook import load_codebook
from app.services.ingestion.workspace import count_document_records
from streamlit_app.runtime_config import sync_streamlit_secrets_to_env

st.set_page_config(page_title="CRM Agreement Intelligence System", layout="wide")
st.title("CRM Agreement Intelligence System")
st.caption("Phase 1 foundation")

sync_streamlit_secrets_to_env()
settings = get_settings()
codebook = load_codebook(settings.active_codebook_path)
local_pdf = Path("CRM Agreements.pdf")
workspace_count = count_document_records()

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Session documents", workspace_count)
col_b.metric("Pending review", 0)
col_c.metric("Discovery candidates", 0)
col_d.metric("Codebook variables", len(codebook.variables))

if local_pdf.exists():
    st.success("Local CRM Agreements.pdf detected. Open New Document Ingestion to extract page-level text.")

st.info(
    "This foundation build supports configuration, document ingestion, page-level PDF extraction, "
    "and the active codebook. AI coding and human review workflows are planned for later phases."
)
