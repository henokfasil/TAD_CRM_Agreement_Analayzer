from __future__ import annotations

import streamlit as st

st.title("New Document Ingestion")
uploaded = st.file_uploader("Upload agreement document", type=["pdf", "docx", "txt"])
if uploaded:
    st.write("Upload API integration is scaffolded; database persistence is the next Phase 1 hardening task.")
    st.write({"filename": uploaded.name, "size_bytes": uploaded.size})

