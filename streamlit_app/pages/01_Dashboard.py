from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion.workspace import load_document_records
from app.services.reporting.exports import build_candidate_provisions, build_workspace_summary
from app.services.review.manual_coding import load_manual_decisions
from app.services.agreements.profiles import load_agreement_profiles
from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.review.adjudication import load_adjudication_decisions
from app.services.verification.ai_verification import load_verification_results

st.title("Dashboard")
records = load_document_records()
decisions = load_manual_decisions()
profiles = load_agreement_profiles()
ai_proposals = load_ai_coding_proposals()
verification_results = load_verification_results()
adjudications = load_adjudication_decisions()
summary = build_workspace_summary(records, decisions, profiles, ai_proposals, verification_results, adjudications)

col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h = st.columns(8)
col_a.metric("Agreements", summary["agreement_profiles"])
col_b.metric("Documents", summary["documents"])
col_c.metric("Pages", summary["pages"])
col_d.metric("Candidate provisions", summary["candidate_provisions"])
col_e.metric("Manual decisions", summary["manual_coding_decisions"])
col_f.metric("AI proposals", summary["ai_coding_proposals"])
col_g.metric("Verifier results", summary["verification_results"])
col_h.metric("Adjudicated", summary["adjudicated_decisions"])

st.caption(
    "Dashboard values currently reflect the prototype workspace. "
    "Validated research indicators will appear after review and database hardening."
)

if decisions:
    st.subheader("Reviewer Status")
    st.bar_chart(summary["reviewer_status_counts"])

    st.subheader("Coded Variables")
    st.bar_chart(summary["coded_variable_counts"])
elif records:
    st.info("Documents are available. Add manual coding decisions in Coding Review to populate charts.")
else:
    st.info("Upload and extract a PDF in New Document Ingestion to populate the dashboard.")

with st.expander("Candidate provision preview"):
    provisions = build_candidate_provisions(records)
    if provisions:
        st.dataframe(
            [
                {
                    "page": provision["page_start"],
                    "method": provision["segmentation_method"],
                    "text": provision["provision_text"][:180],
                }
                for provision in provisions[:25]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No candidate provisions available.")
