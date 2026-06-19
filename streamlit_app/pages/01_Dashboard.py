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

st.title("Dashboard")
records = load_document_records()
decisions = load_manual_decisions()
summary = build_workspace_summary(records, decisions)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Documents", summary["documents"])
col_b.metric("Pages", summary["pages"])
col_c.metric("Candidate provisions", summary["candidate_provisions"])
col_d.metric("Manual decisions", summary["manual_coding_decisions"])

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
