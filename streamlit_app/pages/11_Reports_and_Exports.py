from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion.workspace import load_document_records
from app.services.reporting.exports import build_research_export_bundle, build_workspace_summary
from app.services.review.manual_coding import load_manual_decisions

st.title("Reports and Exports")
records = load_document_records()
decisions = load_manual_decisions()
summary = build_workspace_summary(records, decisions)
bundle = build_research_export_bundle(records, decisions)

st.caption(
    "These exports are prototype workspace outputs. They distinguish manual/provisional review data "
    "from future validated research datasets."
)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Documents", summary["documents"])
col_b.metric("Candidate provisions", summary["candidate_provisions"])
col_c.metric("Manual decisions", summary["manual_coding_decisions"])

st.subheader("Downloads")
downloads = [
    ("Workspace summary JSON", "crm_workspace_summary.json", bundle["summary_json"], "application/json"),
    ("Documents JSON", "crm_documents.json", bundle["documents_json"], "application/json"),
    ("Extracted pages CSV", "crm_extracted_pages.csv", bundle["pages_csv"], "text/csv"),
    (
        "Candidate provisions CSV",
        "crm_candidate_provisions.csv",
        bundle["candidate_provisions_csv"],
        "text/csv",
    ),
    (
        "Manual coding decisions CSV",
        "crm_manual_coding_decisions.csv",
        bundle["manual_decisions_csv"],
        "text/csv",
    ),
]

for label, file_name, payload, mime in downloads:
    st.download_button(label, payload, file_name=file_name, mime=mime)

with st.expander("Workspace summary"):
    st.json(summary)
