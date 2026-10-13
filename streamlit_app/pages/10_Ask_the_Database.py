from __future__ import annotations

import streamlit as st
from streamlit_app.ui import page_header

page_header("Ask the database", "Query the validated agreement corpus in plain language with evidence-linked answers.", eyebrow="Research assistant")
st.info("Semantic questions with citations will be enabled after validated data and embeddings exist.")
