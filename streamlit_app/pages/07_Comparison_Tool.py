from __future__ import annotations

from importlib import reload

import streamlit as st

from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.ingestion.workspace import load_document_records
from app.services.reporting import comparison as comparison_service
from app.services.review.adjudication import load_adjudication_decisions
from app.services.review.manual_coding import load_manual_decisions
from streamlit_app.ui import page_header, workflow_navigation

# Streamlit Cloud may rerun a page in a worker that still holds the previous
# module version after a rapid deployment. Reload keeps page and service code atomic.
comparison_service = reload(comparison_service)

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
    overview_rows = comparison_service.build_document_overview(records)
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

    tab_text, tab_overview, tab_classifications = st.tabs(
        ["Text & themes", "Document facts", "Research classifications"]
    )
    with tab_text:
        if len(selected_records) < 2:
            st.warning("Select at least two agreements.")
        else:
            text_comparison = comparison_service.build_text_comparison(selected_records)
            st.subheader("What the agreements discuss")
            st.dataframe(
                text_comparison["themes"],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                "Numbers are keyword mentions in the extracted text. They show emphasis, not a "
                "validated legal conclusion."
            )

            selected_theme = st.selectbox(
                "Inspect supporting passages for a theme",
                [row["theme"] for row in text_comparison["themes"]],
            )
            evidence_columns = st.columns(len(selected_records))
            for column, record in zip(evidence_columns, selected_records):
                filename = record["original_filename"]
                with column:
                    st.markdown(f"**{filename}**")
                    excerpts = text_comparison["evidence"][selected_theme][filename]
                    if excerpts:
                        for item in excerpts:
                            st.caption(f"Page {item['page']}")
                            st.write(item["excerpt"])
                    else:
                        st.write("No matching passage detected.")

            st.subheader("Overall textual overlap")
            st.dataframe(
                text_comparison["pairwise"],
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Distinctive terms in each agreement"):
                for filename, terms in text_comparison["distinctive_terms"].items():
                    st.markdown(f"**{filename}:** {terms or 'No distinctive terms detected.'}")

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
                "These document facts are available immediately from the uploaded documents. "
                "Candidate-provision counts are machine-generated and remain provisional."
            )

    with tab_classifications:
        comparison_rows = comparison_service.build_classification_comparison(
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
            shared_rows = comparison_service.shared_classification_summary(comparison_rows)
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
