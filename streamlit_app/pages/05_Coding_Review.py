from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.services.classification.rules import evaluate_dependency_rules, summarize_rule_result
from app.services.codebook import load_codebook
from app.services.ingestion.workspace import load_document_records
from app.services.review.manual_coding import (
    build_manual_decision,
    decisions_to_csv,
    load_manual_decisions,
    save_manual_decision,
)
from app.services.review.queue import build_decision_review_queue, build_uncoded_provision_queue
from app.services.segmentation.basic import segment_document_pages

st.title("Coding Review")
st.warning("No AI-generated code is treated as validated until reviewer approval or adjudication.")

settings = get_settings()
codebook = load_codebook(settings.active_codebook_path)
records = load_document_records()
decisions = load_manual_decisions()

tab_review, tab_queue, tab_saved = st.tabs(["Manual Coding", "Review Queue", "Saved Decisions"])

with tab_review:
    if not records:
        st.info("No extracted documents are available. Use New Document Ingestion first.")
    else:
        selected_document_id = st.selectbox(
            "Document",
            [record["document_id"] for record in records],
            format_func=lambda value: next(
                record["original_filename"] for record in records if record["document_id"] == value
            ),
        )
        selected_document = next(
            record for record in records if record["document_id"] == selected_document_id
        )
        provisions = segment_document_pages(selected_document)

        if not provisions:
            st.info("No candidate provisions were detected for this document.")
        else:
            selected_provision_id = st.selectbox(
                "Candidate provision",
                [provision["provision_id"] for provision in provisions],
                format_func=lambda value: next(
                    f"Page {provision['page_start']} | {provision['provision_text'][:90]}"
                    for provision in provisions
                    if provision["provision_id"] == value
                ),
            )
            selected_provision = next(
                provision for provision in provisions if provision["provision_id"] == selected_provision_id
            )

            st.text_area(
                "Provision text",
                selected_provision["provision_text"],
                height=240,
                disabled=True,
            )

            family_options = sorted({variable.family for variable in codebook.variables})
            selected_family = st.selectbox("Codebook family", family_options)
            variable_options = [
                variable for variable in codebook.variables if variable.family == selected_family
            ]
            selected_variable_code = st.selectbox(
                "Variable",
                [variable.code for variable in variable_options],
                format_func=lambda value: next(
                    f"{variable.code} - {variable.label}"
                    for variable in variable_options
                    if variable.code == value
                ),
            )
            selected_variable = next(
                variable for variable in variable_options if variable.code == selected_variable_code
            )

            with st.expander("Variable definition", expanded=True):
                st.write(selected_variable.description)
                st.json(
                    {
                        "allowed_values": selected_variable.allowed_values,
                        "risk_level": selected_variable.risk_level,
                        "mandatory_human_review": selected_variable.mandatory_human_review,
                        "dependencies": selected_variable.dependencies,
                    }
                )

            proposed_value = st.selectbox(
                "Proposed value",
                [str(value) for value in selected_variable.allowed_values],
            )
            reviewer_status = st.selectbox(
                "Reviewer status",
                ["provisional", "approved", "rejected", "uncertain"],
            )
            evidence_quote = st.text_area(
                "Evidence quote",
                selected_provision["provision_text"][:500],
                height=140,
            )
            reviewer_note = st.text_area("Reviewer note", height=100)
            rule_result = evaluate_dependency_rules(
                selected_variable,
                proposed_value,
                decisions,
                selected_provision["provision_id"],
            )
            if rule_result["status"] == "violation":
                st.error(summarize_rule_result(rule_result))
                st.json(rule_result["violations"])
            elif rule_result["status"] == "pass":
                st.success(summarize_rule_result(rule_result))
            else:
                st.caption(summarize_rule_result(rule_result))

            if st.button("Save manual coding decision", type="primary"):
                decision = build_manual_decision(
                    document_id=selected_document["document_id"],
                    provision=selected_provision,
                    variable_code=selected_variable.code,
                    proposed_value=proposed_value,
                    reviewer_status=reviewer_status,
                    evidence_quote=evidence_quote,
                    reviewer_note=reviewer_note,
                )
                save_manual_decision(decision)
                st.success("Manual coding decision saved.")
                st.rerun()

with tab_queue:
    all_provisions = []
    for record in records:
        for provision in segment_document_pages(record):
            provision["document_filename"] = record["original_filename"]
            all_provisions.append(provision)
    uncoded = build_uncoded_provision_queue(all_provisions, decisions)
    pending = build_decision_review_queue(decisions)

    col_q1, col_q2 = st.columns(2)
    col_q1.metric("Uncoded candidate provisions", len(uncoded))
    col_q2.metric("Provisional or uncertain decisions", len(pending))

    queue_view = st.radio("Queue view", ["Uncoded provisions", "Pending decisions"], horizontal=True)
    if queue_view == "Uncoded provisions":
        if uncoded:
            st.dataframe(
                [
                    {
                        "document": provision.get("document_filename"),
                        "page": provision["page_start"],
                        "method": provision["segmentation_method"],
                        "text": provision["provision_text"][:240],
                    }
                    for provision in uncoded
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No uncoded candidate provisions in the current workspace.")
    else:
        if pending:
            st.dataframe(pending, use_container_width=True, hide_index=True)
        else:
            st.success("No provisional or uncertain manual coding decisions.")

with tab_saved:
    st.subheader("Saved Manual Decisions")
    decisions = load_manual_decisions()
    if not decisions:
        st.info("No manual coding decisions saved yet.")
    else:
        st.dataframe(decisions, use_container_width=True, hide_index=True)
        st.download_button(
            "Download manual coding decisions CSV",
            decisions_to_csv(decisions),
            file_name="crm_manual_coding_decisions.csv",
            mime="text/csv",
        )
