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
from streamlit_app.ui import apply_app_style, stat_cards

st.set_page_config(
    page_title="CRM Agreement Intelligence",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_app_style()
sync_streamlit_secrets_to_env()

OECD_LOGO = PROJECT_ROOT / "streamlit_app" / "assets" / "oecd-logo.png"
if OECD_LOGO.exists():
    st.logo(str(OECD_LOGO), size="large", link="https://www.oecd.org/")


def render_home() -> None:
    sync_streamlit_secrets_to_env()
    settings = get_settings()
    codebook = load_codebook(settings.active_codebook_path)
    workspace_count = count_document_records()

    st.markdown(
        """
        <section class="crm-hero">
            <div>
                <div class="crm-kicker">Critical raw materials agreements</div>
                <h1>Turn agreements into trusted research.</h1>
                <p>A calm workspace for reading complex agreements, finding the provisions that matter, and building evidence you can defend.</p>
            </div>
            <div class="crm-paper-stack" aria-hidden="true">
                <div class="crm-paper-back"></div>
                <div class="crm-paper"></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    stat_cards(
        [
            ("Saved agreements", workspace_count, "Persisted source documents"),
            ("Workflow", "6 steps", "From discovery to comparison"),
            ("Review model", "Human-led", "AI suggestions remain provisional"),
            ("Research variables", len(codebook.variables), "Defined in the active codebook"),
        ]
    )

    st.markdown('<div class="crm-section-title">A document becomes evidence in three movements</div>', unsafe_allow_html=True)
    st.markdown('<div class="crm-section-note">The numbered sidebar keeps the detailed steps in order.</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="crm-flow">
            <div class="crm-flow-card"><span class="crm-flow-number">1</span><h3>Bring the source in</h3><p>Upload the official PDF. OCR quietly recovers text from scanned pages.</p></div>
            <div class="crm-flow-card"><span class="crm-flow-number">2</span><h3>Read, classify, and verify</h3><p>Review provisions, assign research categories, and test every claim against evidence.</p></div>
            <div class="crm-flow-card"><span class="crm-flow-number">3</span><h3>Finalise and compare</h3><p>Resolve uncertain results, then compare agreements and export defensible data.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Start with a document", type="primary", use_container_width=True):
        st.switch_page("pages/03_New_Document_Ingestion.py")

    st.info(
        "AI outputs remain provisional until final human review. Every classification decision "
        "retains page-level evidence and provenance."
    )

pages = {
    "Overview": [
        st.Page(render_home, title="Home", icon="🏠", default=True),
        st.Page("pages/01_Dashboard.py", title="Dashboard", icon="📊"),
    ],
    "Research workflow": [
        st.Page("pages/04_Discovery_Queue.py", title="1 · Discover agreements", icon="🔎"),
        st.Page("pages/03_New_Document_Ingestion.py", title="2 · Upload agreements", icon="📄"),
        st.Page("pages/02_Agreement_Explorer.py", title="3 · Review & structure", icon="🧭"),
        st.Page("pages/05_Coding_Review.py", title="4 · Classify & verify", icon="🏷️"),
        st.Page("pages/06_Adjudication.py", title="5 · Final review", icon="✅"),
    ],
    "Analysis & outputs": [
        st.Page("pages/07_Comparison_Tool.py", title="6 · Compare agreements", icon="⚖️"),
        st.Page("pages/08_Network_Analysis.py", title="Network analysis", icon="🕸️"),
        st.Page("pages/09_Implementation_Tracker.py", title="Implementation tracker", icon="📅"),
        st.Page("pages/10_Ask_the_Database.py", title="Ask the database", icon="💬"),
        st.Page("pages/11_Reports_and_Exports.py", title="Reports & exports", icon="📤"),
    ],
    "Research production": [
        st.Page("pages/14_Research_Engine.py", title="Research engine", icon="🧠"),
    ],
    "Meeting room": [
        st.Page("pages/13_Presentation.py", title="Studio presentation", icon="🎬"),
    ],
    "Administration": [
        st.Page("pages/12_Admin_and_Codebook.py", title="Codebook & settings", icon="⚙️"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
