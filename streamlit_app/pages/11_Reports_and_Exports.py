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
from app.services.agreements.profiles import load_agreement_profiles
from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.review.adjudication import load_adjudication_decisions
from app.services.verification.ai_verification import load_verification_results

st.title("Reports and Exports")
records = load_document_records()
decisions = load_manual_decisions()
profiles = load_agreement_profiles()
ai_proposals = load_ai_coding_proposals()
verification_results = load_verification_results()
adjudications = load_adjudication_decisions()
summary = build_workspace_summary(records, decisions, profiles, ai_proposals, verification_results, adjudications)
bundle = build_research_export_bundle(records, decisions, profiles, ai_proposals, verification_results, adjudications)

st.caption(
    "These exports are prototype workspace outputs. They distinguish manual/provisional review data "
    "from future validated research datasets."
)

col_a, col_b, col_c, col_d, col_e, col_f, col_g = st.columns(7)
col_a.metric("Agreements", summary["agreement_profiles"])
col_b.metric("Documents", summary["documents"])
col_c.metric("Candidate provisions", summary["candidate_provisions"])
col_d.metric("Manual decisions", summary["manual_coding_decisions"])
col_e.metric("AI proposals", summary["ai_coding_proposals"])
col_f.metric("Verifier results", summary["verification_results"])
col_g.metric("Adjudicated", summary["adjudicated_decisions"])

st.subheader("Downloads")
downloads = [
    ("Workspace summary JSON", "crm_workspace_summary.json", bundle["summary_json"], "application/json"),
    ("Agreement profiles CSV", "crm_agreement_profiles.csv", bundle["agreement_profiles_csv"], "text/csv"),
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
    (
        "AI coding proposals CSV",
        "crm_ai_coding_proposals.csv",
        bundle["ai_proposals_csv"],
        "text/csv",
    ),
    (
        "Verification results CSV",
        "crm_ai_verification_results.csv",
        bundle["verification_results_csv"],
        "text/csv",
    ),
    (
        "Adjudication decisions CSV",
        "crm_adjudication_decisions.csv",
        bundle["adjudications_csv"],
        "text/csv",
    ),
]

for label, file_name, payload, mime in downloads:
    st.download_button(label, payload, file_name=file_name, mime=mime)

with st.expander("Workspace summary"):
    st.json(summary)
