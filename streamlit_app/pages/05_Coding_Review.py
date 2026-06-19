from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.llm.errors import ExternalLLMDisabledError
from app.llm.registry import load_model_registry, resolve_runtime_model_config
from app.services.classification.ai_coding import (
    ai_proposals_to_csv,
    load_ai_coding_proposals,
    run_batch_ai_coding_proposals,
    run_ai_coding_proposal,
    save_ai_coding_proposal,
)
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
from app.services.verification.ai_verification import (
    load_verification_results,
    run_mock_verification,
    save_verification_result,
    verification_results_to_csv,
)
from streamlit_app.runtime_config import sync_streamlit_secrets_to_env

st.title("Coding Review")
st.warning("No AI-generated code is treated as validated until reviewer approval or adjudication.")

sync_streamlit_secrets_to_env()
settings = get_settings()
codebook = load_codebook(settings.active_codebook_path)
model_registry = load_model_registry("config/models/model_registry.yaml")
records = load_document_records()
decisions = load_manual_decisions()
ai_proposals = load_ai_coding_proposals()
verification_results = load_verification_results()

tab_review, tab_ai, tab_verify, tab_queue, tab_saved = st.tabs(
    ["Manual Coding", "AI Proposal", "Verification", "Review Queue", "Saved Decisions"]
)

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

with tab_ai:
    st.caption("AI outputs are saved as provisional proposals requiring review.")
    model_options = list(model_registry.models.keys())
    selected_model_key = st.selectbox(
        "AI model configuration",
        model_options,
        format_func=lambda key: (
            f"{key} | "
            f"{resolve_runtime_model_config(model_registry.models[key]).provider} | "
            f"{resolve_runtime_model_config(model_registry.models[key]).model_name}"
        ),
    )
    selected_model_config = resolve_runtime_model_config(model_registry.models[selected_model_key])
    if selected_model_config.provider == "openai_compatible":
        if settings.allow_external_llm and settings.openai_api_key:
            st.success("OpenAI calls are enabled for this session.")
        else:
            st.warning(
                "OpenAI is configured in the registry but disabled until "
                "ALLOW_EXTERNAL_LLM=true and OPENAI_API_KEY are set."
            )
    elif selected_model_config.provider == "gemini":
        if settings.allow_external_llm and settings.gemini_api_key:
            st.success("Gemini calls are enabled for this session.")
        else:
            st.warning(
                "Gemini is configured in the registry but disabled until "
                "ALLOW_EXTERNAL_LLM=true and GEMINI_API_KEY are set."
            )
    if not records:
        st.info("No extracted documents are available. Use New Document Ingestion first.")
    else:
        selected_document_id = st.selectbox(
            "AI document",
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
                "AI candidate provision",
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
            st.text_area("AI provision text", selected_provision["provision_text"], height=220, disabled=True)

            family_options = sorted({variable.family for variable in codebook.variables})
            selected_family = st.selectbox("AI codebook family", family_options)
            variable_options = [
                variable for variable in codebook.variables if variable.family == selected_family
            ]
            selected_variable_code = st.selectbox(
                "AI variable",
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

            run_mode = st.radio(
                "AI run mode",
                ["Single provision", "Batch provisions"],
                horizontal=True,
            )

            if run_mode == "Single provision" and st.button("Run AI proposal", type="primary"):
                try:
                    proposal = run_ai_coding_proposal(
                        document_id=selected_document["document_id"],
                        provision=selected_provision,
                        variable=selected_variable,
                        existing_decisions=decisions,
                        codebook_version=codebook.version,
                        model_key=selected_model_key,
                    )
                except ExternalLLMDisabledError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"AI proposal failed: {exc}")
                else:
                    save_ai_coding_proposal(proposal)
                    st.success("AI proposal saved as pending and unverified.")
                    st.json(proposal)
                    st.rerun()

            if run_mode == "Batch provisions":
                st.caption(
                    "Batch proposals are capped and saved as pending. Review, verify, and adjudicate "
                    "before treating any value as final."
                )
                batch_limit = st.slider(
                    "Maximum candidate provisions to process",
                    min_value=1,
                    max_value=min(20, len(provisions)),
                    value=min(5, len(provisions)),
                )
                skip_existing = st.checkbox(
                    "Skip provisions already proposed with this model and variable",
                    value=True,
                )
                if st.button("Run batch AI proposals", type="primary"):
                    try:
                        result = run_batch_ai_coding_proposals(
                            document_id=selected_document["document_id"],
                            provisions=provisions,
                            variable=selected_variable,
                            existing_decisions=decisions,
                            existing_proposals=ai_proposals,
                            codebook_version=codebook.version,
                            model_key=selected_model_key,
                            limit=batch_limit,
                            skip_existing=skip_existing,
                        )
                    except ExternalLLMDisabledError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Batch AI proposal failed: {exc}")
                    else:
                        for proposal in result["created"]:
                            save_ai_coding_proposal(proposal)
                        st.success(
                            f"Saved {len(result['created'])} pending AI proposals; "
                            f"skipped {len(result['skipped'])}."
                        )
                        if result["errors"]:
                            st.warning("Batch stopped after an error.")
                            st.json(result["errors"])
                        if result["created"]:
                            st.dataframe(
                                [
                                    {
                                        "provision_id": proposal["provision_id"],
                                        "variable": proposal["variable_code"],
                                        "value": proposal["proposed_value"],
                                        "confidence": proposal["confidence"],
                                        "rule_status": proposal["rule_status"],
                                    }
                                    for proposal in result["created"]
                                ],
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.info("No new AI proposals were created in this batch.")

with tab_verify:
    st.caption("Verifier outputs are independent checks on AI proposals and still require human review.")
    ai_proposals = load_ai_coding_proposals()
    if not ai_proposals:
        st.info("No AI proposals are available to verify.")
    else:
        selected_proposal_id = st.selectbox(
            "AI proposal",
            [proposal["proposal_id"] for proposal in ai_proposals],
            format_func=lambda value: next(
                f"{proposal['variable_code']}={proposal['proposed_value']} | "
                f"{proposal['model_provider']} | {proposal['rule_status']}"
                for proposal in ai_proposals
                if proposal["proposal_id"] == value
            ),
        )
        selected_proposal = next(
            proposal for proposal in ai_proposals if proposal["proposal_id"] == selected_proposal_id
        )
        st.json(
            {
                "variable_code": selected_proposal["variable_code"],
                "proposed_value": selected_proposal["proposed_value"],
                "confidence": selected_proposal["confidence"],
                "rule_status": selected_proposal["rule_status"],
                "evidence_page": selected_proposal["evidence_page"],
                "evidence_quote": selected_proposal["evidence_quote"],
            }
        )
        if st.button("Run mock verifier", type="primary"):
            result = run_mock_verification(selected_proposal)
            save_verification_result(result)
            st.success("Mock verification result saved.")
            st.json(result)
            st.rerun()

with tab_queue:
    all_provisions = []
    for record in records:
        for provision in segment_document_pages(record):
            provision["document_filename"] = record["original_filename"]
            all_provisions.append(provision)
    uncoded = build_uncoded_provision_queue(all_provisions, decisions)
    pending = build_decision_review_queue(decisions)
    pending_ai = [proposal for proposal in ai_proposals if proposal["reviewer_status"] == "pending"]
    unverified_ai = [
        proposal
        for proposal in ai_proposals
        if proposal["proposal_id"] not in {result["proposal_id"] for result in verification_results}
    ]

    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    col_q1.metric("Uncoded candidate provisions", len(uncoded))
    col_q2.metric("Provisional or uncertain decisions", len(pending))
    col_q3.metric("Pending AI proposals", len(pending_ai))
    col_q4.metric("Unverified AI proposals", len(unverified_ai))

    queue_view = st.radio(
        "Queue view",
        ["Uncoded provisions", "Pending decisions", "Pending AI proposals", "Unverified AI proposals"],
        horizontal=True,
    )
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
        if queue_view == "Pending decisions" and pending:
            st.dataframe(pending, use_container_width=True, hide_index=True)
        elif queue_view == "Pending AI proposals" and pending_ai:
            st.dataframe(pending_ai, use_container_width=True, hide_index=True)
        elif queue_view == "Unverified AI proposals" and unverified_ai:
            st.dataframe(unverified_ai, use_container_width=True, hide_index=True)
        elif queue_view == "Pending decisions":
            st.success("No provisional or uncertain manual coding decisions.")
        elif queue_view == "Pending AI proposals":
            st.success("No pending AI proposals.")
        else:
            st.success("No unverified AI proposals.")

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
    st.subheader("Saved AI Proposals")
    ai_proposals = load_ai_coding_proposals()
    if not ai_proposals:
        st.info("No AI coding proposals saved yet.")
    else:
        st.dataframe(ai_proposals, use_container_width=True, hide_index=True)
        st.download_button(
            "Download AI proposals CSV",
            ai_proposals_to_csv(ai_proposals),
            file_name="crm_ai_coding_proposals.csv",
            mime="text/csv",
        )
    st.subheader("Saved Verification Results")
    verification_results = load_verification_results()
    if not verification_results:
        st.info("No verification results saved yet.")
    else:
        st.dataframe(verification_results, use_container_width=True, hide_index=True)
        st.download_button(
            "Download verification results CSV",
            verification_results_to_csv(verification_results),
            file_name="crm_ai_verification_results.csv",
            mime="text/csv",
        )
