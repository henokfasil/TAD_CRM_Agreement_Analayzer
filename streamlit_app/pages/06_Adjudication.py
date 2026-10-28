from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.agreements.profiles import load_agreement_document_links, load_agreement_profiles  # noqa: E402
from app.services.classification.ai_coding import load_ai_coding_proposals  # noqa: E402
from app.services.ingestion.workspace import load_document_records  # noqa: E402
from app.services.research.answer_sheet import (  # noqa: E402
    ANSWER_OPTIONS,
    build_agreement_approval,
    build_answer_sheet,
    build_question_review,
    load_agreement_approvals,
    load_question_reviews,
    save_agreement_approval,
    save_question_review,
)
from app.services.review.adjudication import (  # noqa: E402
    adjudications_to_csv,
    build_adjudication_decision,
    load_adjudication_decisions,
    save_adjudication_decision,
)
from app.services.review.manual_coding import load_manual_decisions  # noqa: E402
from streamlit_app.ui import page_header, stat_cards, workflow_navigation  # noqa: E402


page_header(
    "Final review",
    "Turn detailed classifications into nine evidence-linked answers, then approve the agreement research profile.",
    eyebrow="Step 5 of 6",
)
st.caption(
    "The answer sheet is the readable research product. Detailed variable adjudication remains "
    "available for verification and methodological audit."
)

documents = load_document_records()
profiles = load_agreement_profiles()
links = load_agreement_document_links()
manual_decisions = load_manual_decisions()
ai_proposals = load_ai_coding_proposals()
adjudications = load_adjudication_decisions()
question_reviews = load_question_reviews()
agreement_approvals = load_agreement_approvals()

tab_profile, tab_detail, tab_saved = st.tabs(
    ["Agreement answer sheet", "Detailed decisions", "Saved final decisions"]
)

with tab_profile:
    if not documents:
        st.info("Upload an agreement before creating its final research profile.")
    else:
        selected_document_id = st.selectbox(
            "Agreement",
            [document["document_id"] for document in documents],
            format_func=lambda value: next(
                document["original_filename"]
                for document in documents
                if document["document_id"] == value
            ),
        )
        selected_document = next(
            document for document in documents if document["document_id"] == selected_document_id
        )
        answers = build_answer_sheet(
            document_id=selected_document_id,
            profiles=profiles,
            links=links,
            adjudications=adjudications,
            manual_decisions=manual_decisions,
            ai_proposals=ai_proposals,
            reviews=question_reviews,
        )
        validated_count = sum(
            answer["validation_status"] == "validated" for answer in answers
        )
        approval = next(
            (
                item
                for item in agreement_approvals
                if item.get("document_id") == selected_document_id
                and item.get("validation_status") == "approved"
            ),
            None,
        )

        stat_cards(
            [
                ("Research questions", len(answers), "The agreed comparative-mapping questions"),
                ("Human validated", validated_count, "Answers reviewed with a rationale"),
                (
                    "Evidence passages",
                    sum(len(answer["evidence"]) for answer in answers),
                    "Page-linked quotations supporting the answers",
                ),
                (
                    "Agreement status",
                    "Approved" if approval else "In review",
                    "Whole-profile publication gate",
                ),
            ]
        )

        if approval:
            st.success(
                f"This agreement research profile was approved by "
                f"{approval.get('reviewer_id', 'a reviewer')}.",
                icon=":material/verified:",
            )
        elif validated_count < len(answers):
            st.warning(
                f"{len(answers) - validated_count} question(s) still require human review. "
                "Provisional answers cannot enter final comparisons or reports.",
                icon=":material/pending_actions:",
            )

        st.markdown(
            f"<div class='crm-result-panel'><div class='crm-result-heading'>"
            f"<span class='crm-result-check'>9</span><div>"
            f"<div class='crm-result-kicker'>Agreement research profile</div>"
            f"<h3>{escape(selected_document['original_filename'])}</h3></div>"
            f"<span class='crm-status-pill'>{validated_count}/9 reviewed</span></div>"
            f"<p style='margin:1rem 0 0;color:var(--crm-muted)'>"
            f"Review each direct answer against its page-level evidence. Save a rationale even "
            f"when the correct result is No or Unclear.</p></div>",
            unsafe_allow_html=True,
        )

        for index, answer in enumerate(answers, start=1):
            icon = "✅" if answer["validation_status"] == "validated" else "🟠"
            with st.expander(
                f"{icon} {index}. {answer['question']} — {answer['answer']}",
                expanded=index == 1 and answer["validation_status"] != "validated",
            ):
                status_text = (
                    "Human validated"
                    if answer["validation_status"] == "validated"
                    else "Provisional synthesis — human review required"
                )
                st.caption(status_text)
                st.markdown(f"**Current synthesis:** {answer['summary']}")

                if answer["evidence"]:
                    st.markdown("**Supporting evidence**")
                    for item in answer["evidence"]:
                        page = item.get("page") or "?"
                        st.markdown(f"> Page {page} · {item['variable']}: “{item['quote']}”")
                else:
                    st.info(
                        "No page quotation is attached yet. A final positive claim should normally "
                        "be supported by evidence from Step 4."
                    )

                if answer["variables"]:
                    with st.popover("View contributing codebook variables"):
                        st.dataframe(answer["variables"], hide_index=True)

                with st.form(f"question_review_{selected_document_id}_{answer['question_id']}"):
                    answer_index = (
                        ANSWER_OPTIONS.index(answer["answer"])
                        if answer["answer"] in ANSWER_OPTIONS
                        else ANSWER_OPTIONS.index("Unclear")
                    )
                    final_answer = st.selectbox(
                        "Final answer", ANSWER_OPTIONS, index=answer_index
                    )
                    final_summary = st.text_area(
                        "Research answer",
                        value=answer["summary"],
                        height=110,
                        help="Write the concise agreement-level answer for comparisons and reports.",
                    )
                    rationale = st.text_area(
                        "Reviewer rationale",
                        value=answer["rationale"],
                        height=90,
                        help="Explain why the answer follows from the evidence or its absence.",
                    )
                    reviewer_id = st.text_input("Reviewer ID", value="prototype_reviewer")
                    submitted = st.form_submit_button("Validate this answer", type="primary")
                    if submitted:
                        if final_answer == "Not reviewed":
                            st.error("Choose a substantive answer before validation.")
                        elif not final_summary.strip() or not rationale.strip():
                            st.error("Both the research answer and reviewer rationale are required.")
                        else:
                            save_question_review(
                                build_question_review(
                                    selected_document_id,
                                    answer["question_id"],
                                    final_answer,
                                    final_summary,
                                    rationale,
                                    reviewer_id,
                                )
                            )
                            st.success("Answer validated and saved.")
                            st.rerun()

        st.divider()
        st.subheader("Approve the complete agreement profile")
        if validated_count == len(answers):
            with st.form(f"approve_profile_{selected_document_id}"):
                approval_reviewer = st.text_input(
                    "Approving reviewer ID", value="prototype_reviewer"
                )
                approval_rationale = st.text_area(
                    "Whole-profile approval note",
                    placeholder="Confirm that all nine answers and their evidence have been reviewed.",
                )
                if st.form_submit_button(
                    "Approve agreement research profile",
                    type="primary",
                    disabled=bool(approval),
                ):
                    if not approval_rationale.strip():
                        st.error("An approval note is required.")
                    else:
                        save_agreement_approval(
                            build_agreement_approval(
                                selected_document_id,
                                approval_reviewer,
                                approval_rationale,
                            )
                        )
                        st.success("Agreement research profile approved.")
                        st.rerun()
        else:
            st.info("Validate all nine answers before approving the complete profile.")

with tab_detail:
    st.subheader("Detailed variable adjudication")
    st.caption(
        "Resolve individual manual classifications or AI suggestions here. The nine-question "
        "answer sheet is the primary research-facing output."
    )
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
        selected_source = next(
            source for source in sources if source[source_id_key] == selected_source_id
        )
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
            placeholder="Explain why this value best matches the agreement evidence.",
        )
        if st.button("Save detailed final decision", type="primary"):
            if not rationale.strip():
                st.error("Rationale is required.")
            else:
                save_adjudication_decision(
                    build_adjudication_decision(
                        source_type,
                        selected_source,
                        final_value,
                        rationale,
                        adjudicator_id,
                    )
                )
                st.success("Detailed final decision saved.")
                st.rerun()

with tab_saved:
    saved_tab, profile_tab = st.tabs(["Variable decisions", "Approved profiles"])
    with saved_tab:
        if not adjudications:
            st.info("No detailed final decisions saved yet.")
        else:
            st.metric("Detailed final decisions", len(adjudications))
            st.dataframe(adjudications, width="stretch", hide_index=True)
            st.download_button(
                "Download final decisions CSV",
                adjudications_to_csv(adjudications),
                file_name="crm_adjudication_decisions.csv",
                mime="text/csv",
            )
    with profile_tab:
        if not agreement_approvals:
            st.info("No complete agreement profiles have been approved yet.")
        else:
            st.dataframe(agreement_approvals, width="stretch", hide_index=True)

workflow_navigation(
    previous=("Classify & verify", "pages/05_Coding_Review.py"),
    next_step=("Compare agreements", "pages/07_Comparison_Tool.py"),
    note="Final comparisons should use complete, human-approved agreement profiles.",
)
