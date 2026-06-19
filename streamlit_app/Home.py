from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="CRM Agreement Intelligence System", layout="wide")
st.title("CRM Agreement Intelligence System")
st.caption("Phase 1 foundation")

st.metric("Validated agreements", 0)
st.metric("Pending review", 0)
st.metric("Discovery candidates", 0)

st.info(
    "This foundation build supports configuration, document ingestion, page-level PDF extraction, "
    "and the active codebook. AI coding and human review workflows are planned for later phases."
)

