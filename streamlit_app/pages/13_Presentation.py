from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from streamlit_app.ui import page_header


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRESENTATION_PATH = PROJECT_ROOT / "streamlit_app" / "assets" / "studio_presentation.html"
LOGO_PATH = PROJECT_ROOT / "streamlit_app" / "assets" / "oecd-logo.png"


def load_presentation() -> str:
    """Load the portable deck and embed its local logo."""
    html = PRESENTATION_PATH.read_text(encoding="utf-8")
    logo_uri = ""
    if LOGO_PATH.exists():
        encoded_logo = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        logo_uri = f"data:image/png;base64,{encoded_logo}"
    return html.replace("oecd-logo.png", logo_uri)


page_header(
    "Studio presentation",
    "A meeting-ready story of the research problem, workflow, safeguards, and path to scale.",
    eyebrow="Presentation mode",
)

presentation_html = load_presentation()
download_column, help_column = st.columns(2)
with download_column:
    st.download_button(
        "Download portable HTML presentation",
        data=presentation_html,
        file_name="crm_agreement_studio_presentation.html",
        mime="text/html",
        width="stretch",
    )
with help_column:
    st.info("Click inside the deck, then use **← →**. Press **N** for notes or **F** for fullscreen.")

encoded_presentation = base64.b64encode(presentation_html.encode("utf-8")).decode("ascii")
st.iframe(
    f"data:text/html;base64,{encoded_presentation}",
    height=780,
)

with st.expander("Suggested meeting flow"):
    st.markdown(
        """
        1. Present through slide 7 in approximately six minutes.
        2. Use the live Studio for a five-minute demonstration after slide 7.
        3. Return to slides 8–10 for the research-engine goal, roadmap, decision, and discussion.

        The deck deliberately distinguishes validated research from provisional AI output.
        """
    )
