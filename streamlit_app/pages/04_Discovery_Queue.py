from __future__ import annotations

import streamlit as st
from streamlit_app.ui import page_header, workflow_navigation

page_header("Discover agreements", "Build a traceable queue of candidate agreements from official sources before ingestion.", eyebrow="Step 1 of 6")
st.info("Scheduled official-source discovery is planned for a later phase. For now, start with a known official document in Ingest documents.")
workflow_navigation(
    next_step=("Ingest documents", "pages/03_New_Document_Ingestion.py"),
    note="Continue with an official agreement PDF you already have.",
)
