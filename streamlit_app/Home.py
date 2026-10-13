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
from streamlit_app.ui import apply_app_style

st.set_page_config(
    page_title="CRM Agreement Intelligence",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_app_style()


def render_home() -> None:
    sync_streamlit_secrets_to_env()
    settings = get_settings()
    codebook = load_codebook(settings.active_codebook_path)
    workspace_count = count_document_records()

    st.markdown(
        """
        <section class="crm-hero">
            <div class="crm-kicker">Critical raw materials agreements</div>
            <h1>From source documents to defensible evidence.</h1>
            <p>Collect, structure, code, verify, and compare international CRM agreements in one transparent human-in-the-loop research workspace.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Workspace documents", workspace_count)
    col_b.metric("Workflow stage", "Research prototype")
    col_c.metric("Review model", "Human-in-the-loop")
    col_d.metric("Codebook variables", len(codebook.variables))

    st.subheader("Research workflow")
    st.caption("Follow the numbered pages in the sidebar, or start directly with a document.")
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.markdown("#### 1–2 · Find and ingest")
        st.write("Register official sources, upload PDFs, and recover scanned text with local OCR.")
    with col_2:
        st.markdown("#### 3–5 · Structure and decide")
        st.write("Review provisions, create coding proposals, verify evidence, and adjudicate.")
    with col_3:
        st.markdown("#### 6 · Analyse and export")
        st.write("Compare validated results, inspect relationships, and export research datasets.")

    if st.button("Start with a document", type="primary", use_container_width=True):
        st.switch_page("pages/03_New_Document_Ingestion.py")

    st.info(
        "AI outputs remain provisional until human review or adjudication. Every coding decision "
        "retains page-level evidence and provenance."
    )

pages = {
    "Overview": [
        st.Page(render_home, title="Home", icon="🏠", default=True),
        st.Page("pages/01_Dashboard.py", title="Dashboard", icon="📊"),
    ],
    "Research workflow": [
        st.Page("pages/04_Discovery_Queue.py", title="1 · Discover agreements", icon="🔎"),
        st.Page("pages/03_New_Document_Ingestion.py", title="2 · Ingest documents", icon="📄"),
        st.Page("pages/02_Agreement_Explorer.py", title="3 · Review & structure", icon="🧭"),
        st.Page("pages/05_Coding_Review.py", title="4 · Code & verify", icon="🏷️"),
        st.Page("pages/06_Adjudication.py", title="5 · Adjudicate", icon="✅"),
    ],
    "Analysis & outputs": [
        st.Page("pages/07_Comparison_Tool.py", title="6 · Compare agreements", icon="⚖️"),
        st.Page("pages/08_Network_Analysis.py", title="Network analysis", icon="🕸️"),
        st.Page("pages/09_Implementation_Tracker.py", title="Implementation tracker", icon="📅"),
        st.Page("pages/10_Ask_the_Database.py", title="Ask the database", icon="💬"),
        st.Page("pages/11_Reports_and_Exports.py", title="Reports & exports", icon="📤"),
    ],
    "Administration": [
        st.Page("pages/12_Admin_and_Codebook.py", title="Codebook & settings", icon="⚙️"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
