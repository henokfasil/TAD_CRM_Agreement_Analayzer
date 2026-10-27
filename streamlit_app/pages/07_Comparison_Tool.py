from __future__ import annotations

import streamlit as st

from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.ingestion.workspace import load_document_records
from app.services.reporting.comparison import (
    build_classification_comparison,
    build_document_overview,
    shared_classification_summary,
)
from app.services.review.adjudication import load_adjudication_decisions
from app.services.review.manual_coding import load_manual_decisions
from streamlit_app.ui import page_header, workflow_navigation

page_header(
    "Compare agreements",
    "Compare uploaded agreements now, then refine the view as classifications are reviewed.",
    eyebrow="Step 6 of 6",
)

records = load_document_records()
if len(records) < 2:
    st.info("Upload at least two agreements to begin a comparison.")
else:
    st.success(f"{len(records)} agreements are available for comparison.")
    overview_rows = build_document_overview(records)
    selected_ids = st.multiselect(
        "Agreements to compare",
        [record["document_id"] for record in records],
        default=[record["document_id"] for record in records],
        format_func=lambda value: next(
            record["original_filename"] for record in records if record["document_id"] == value
        ),
    )
    selected_records = [record for record in records if record["document_id"] in selected_ids]
    selected_overview = [row for row in overview_rows if row["document_id"] in selected_ids]

    tab_overview, tab_classifications = st.tabs(["Document comparison", "Research classifications"])
    with tab_overview:
        if len(selected_records) < 2:
            st.warning("Select at least two agreements.")
        else:
            st.dataframe(
                [
                    {key: value for key, value in row.items() if key != "document_id"}
                    for row in selected_overview
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "This comparison is available immediately from the uploaded documents. "
                "Candidate-provision counts are machine-generated and remain provisional."
            )

    with tab_classifications:
        comparison_rows = build_classification_comparison(
            selected_records,
            load_adjudication_decisions(),
            load_manual_decisions(),
            load_ai_coding_proposals(),
        )
        if not comparison_rows:
            st.info(
                "No classifications exist yet. The document comparison above still works; "
                "classify provisions in Step 4 to add variable-by-variable results here."
            )
        else:
            shared_rows = shared_classification_summary(comparison_rows)
            show_shared_only = st.toggle(
                "Only variables classified in more than one agreement",
                value=bool(shared_rows),
            )
            display_rows = shared_rows if show_shared_only else comparison_rows
            if display_rows:
                st.dataframe(display_rows, use_container_width=True, hide_index=True)
                st.caption(
                    "Status distinguishes AI proposals, manual classifications, and "
                    "human-approved results. Human-approved values take precedence."
                )
            else:
                st.warning(
                    "No shared classified variables yet. Turn off the filter to see all results."
                )

workflow_navigation(
    previous=("Adjudicate", "pages/06_Adjudication.py"),
    note="This is the final numbered workflow step. Document comparison starts with two uploads; reviewed classifications deepen it.",
)
