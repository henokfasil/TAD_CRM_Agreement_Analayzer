from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.review.adjudication import (
    adjudications_to_csv,
    build_adjudication_decision,
    load_adjudication_decisions,
    save_adjudication_decision,
)
from app.services.review.manual_coding import load_manual_decisions
from streamlit_app.ui import page_header, workflow_navigation

page_header(
    "Final review",
    "Resolve provisional or conflicting classifications into a documented human decision with a short rationale.",
    eyebrow="Step 5 of 6",
)
st.caption(
    "Final review records the accepted value and your reason while preserving the original manual "
    "classification or AI suggestion."
)

manual_decisions = load_manual_decisions()
ai_proposals = load_ai_coding_proposals()
adjudications = load_adjudication_decisions()

tab_create, tab_saved = st.tabs(["Make final decision", "Saved final decisions"])

with tab_create:
    source_type = st.radio("Source type", ["manual", "ai"], horizontal=True)
    sources = manual_decisions if source_type == "manual" else ai_proposals
    source_id_key = "decision_id" if source_type == "manual" else "proposal_id"

    if not sources:
        st.info(f"No {source_type} source records are available.")
    else:
        selected_source_id = st.selectbox(
            "Source record",
            [source[source_id_key] for source in sources],
            format_func=lambda value: next(
                f"{source['variable_code']}={source['proposed_value']} | "
                f"{source.get('reviewer_status', 'pending')}"
                for source in sources
                if source[source_id_key] == value
            ),
        )
        selected_source = next(source for source in sources if source[source_id_key] == selected_source_id)
        st.json(
            {
                "document_id": selected_source["document_id"],
                "provision_id": selected_source["provision_id"],
                "variable_code": selected_source["variable_code"],
                "proposed_value": selected_source["proposed_value"],
                "evidence_page": selected_source.get("evidence_page"),
                "evidence_quote": selected_source.get("evidence_quote"),
            }
        )

        final_value = st.text_input("Final value", value=str(selected_source["proposed_value"]))
        adjudicator_id = st.text_input("Reviewer ID", value="prototype_reviewer")
        rationale = st.text_area(
            "Reason for the final decision",
            height=140,
            placeholder="Explain briefly why this value best matches the agreement evidence.",
        )

        if st.button("Save final decision", type="primary"):
            if not rationale.strip():
                st.error("Rationale is required.")
            else:
                decision = build_adjudication_decision(
                    source_type=source_type,
                    source=selected_source,
                    final_value=final_value,
                    rationale=rationale,
                    adjudicator_id=adjudicator_id,
                )
                save_adjudication_decision(decision)
                st.success("Final decision saved.")
                st.rerun()

with tab_saved:
    if not adjudications:
        st.info("No final decisions saved yet.")
    else:
        st.metric("Final decisions", len(adjudications))
        st.dataframe(adjudications, use_container_width=True, hide_index=True)
        st.download_button(
            "Download final decisions CSV",
            adjudications_to_csv(adjudications),
            file_name="crm_adjudication_decisions.csv",
            mime="text/csv",
        )

workflow_navigation(
    previous=("Classify & verify", "pages/05_Coding_Review.py"),
    next_step=("Compare agreements", "pages/07_Comparison_Tool.py"),
    note="Return to classification if evidence needs revision, or continue with validated decisions.",
)
