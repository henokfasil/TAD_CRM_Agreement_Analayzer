from __future__ import annotations

import streamlit as st
from streamlit_app.ui import page_header, workflow_navigation

page_header("Compare agreements", "Examine validated similarities and differences across agreements, parties, and coded provisions.", eyebrow="Step 6 of 6")
st.info("Validated agreement comparisons will become available as adjudicated records accumulate.")
workflow_navigation(
    previous=("Adjudicate", "pages/06_Adjudication.py"),
    note="This is the final numbered workflow step. Continue to reports when the comparison outputs are ready.",
)
