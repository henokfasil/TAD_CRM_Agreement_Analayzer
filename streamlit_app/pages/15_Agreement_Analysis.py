from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.llm.errors import ExternalLLMDisabledError, ExternalLLMRequestError  # noqa: E402
from app.services.ingestion.workspace import load_document_records  # noqa: E402
from app.services.research.automatic_analysis import (  # noqa: E402
    available_analysis_models,
    latest_analysis_by_document,
    load_agreement_analyses,
    run_agreement_analysis,
    save_agreement_analysis,
)
from streamlit_app.runtime_config import sync_streamlit_secrets_to_env  # noqa: E402
from streamlit_app.ui import page_header, stat_cards, workflow_navigation  # noqa: E402


sync_streamlit_secrets_to_env()
if os.environ.get("GEMINI_MODEL", "").strip().lower() in {
    "gemini-3.5-flash",
    "gemini-flash-latest",
}:
    os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
get_settings.cache_clear()
settings = get_settings()

page_header(
    "Analyse agreements",
    "Generate nine evidence-linked research answers from a saved agreement in one structured run.",
    eyebrow="Step 2 of 4",
)
st.caption(
    "The analysis is provisional. Quotations are checked against the extracted pages, and a human "
    "must approve the answers before they enter comparisons or reports."
)

documents = load_document_records()
analyses = load_agreement_analyses()
latest = latest_analysis_by_document(analyses)
models = available_analysis_models()
models = {
    key: (
        model.model_copy(update={"model_name": "gemini-2.5-flash"})
        if model.provider == "gemini"
        and model.model_name in {"gemini-3.5-flash", "gemini-flash-latest"}
        else model
    )
    for key, model in models.items()
}

if not documents:
    st.info("Upload an agreement before running research analysis.")
else:
    selected_document_id = st.selectbox(
        "Agreement to analyse",
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
    readable_pages = sum(
        bool(str(page.get("text", "")).strip()) for page in selected_document.get("pages", [])
    )
    current = latest.get(selected_document_id)

    stat_cards(
        [
            ("Readable pages", f"{readable_pages}/{selected_document['page_count']}", "Available to the analyser"),
            ("Research questions", 9, "Answered together in one run"),
            (
                "Analysis status",
                "Ready for review" if current else "Not analysed",
                "Saved persistently with model provenance",
            ),
            (
                "Evidence checks",
                sum(len(answer.get("evidence", [])) for answer in (current or {}).get("answers", [])),
                "Quotations confirmed against extracted pages",
            ),
        ]
    )

    if current:
        st.success(
            f"A provisional analysis is saved from {current.get('model_provider')} / "
            f"{current.get('model_name')}. You may review it below or run a fresh analysis."
        )
    else:
        st.info(
            "This agreement has readable text but no research analysis yet. Run the analyser to "
            "populate the nine-question review sheet."
        )

    configured_models = {}
    for key, model in models.items():
        if model.provider == "gemini" and settings.allow_external_llm and settings.gemini_api_key:
            configured_models[key] = model
        elif (
            model.provider == "openai_compatible"
            and settings.allow_external_llm
            and settings.openai_api_key
        ):
            configured_models[key] = model

    if configured_models:
        selected_model_key = st.selectbox(
            "Analysis model",
            list(configured_models),
            format_func=lambda key: (
                f"{configured_models[key].provider} · {configured_models[key].model_name}"
            ),
        )
        st.caption("The model alias is resolved to a currently supported provider endpoint.")
        button_label = "Re-analyse agreement" if current else "Analyse agreement"
        if st.button(
            button_label,
            type="primary",
            disabled=readable_pages == 0,
            width="stretch",
        ):
            try:
                with st.status("Reading the agreement and answering nine questions…", expanded=True) as status:
                    st.write("Preparing page-labelled agreement text")
                    st.write("Extracting participants and agreement metadata")
                    selected_model = configured_models[selected_model_key]
                    if selected_model.provider == "gemini":
                        os.environ["GEMINI_MODEL"] = selected_model.model_name
                        get_settings.cache_clear()
                    analysis = run_agreement_analysis(selected_document, selected_model_key)
                    st.write("Checking every quotation against the saved pages")
                    save_agreement_analysis(analysis)
                    status.update(label="Analysis saved and ready for human review", state="complete")
            except (ExternalLLMDisabledError, ExternalLLMRequestError, ValueError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"The agreement analysis could not be completed: {exc}")
            else:
                st.rerun()
    else:
        st.error(
            "No external analysis model is enabled. Add either Gemini or OpenAI credentials in "
            "Streamlit Secrets and set ALLOW_EXTERNAL_LLM=true. The stored PDF remains safe."
        )

    if current:
        profile = current.get("profile", {})
        st.subheader("Latest provisional analysis")
        participants = [*(profile.get("countries") or []), *(profile.get("organisations") or [])]
        st.write(
            f"**Participants:** {', '.join(participants) if participants else 'Unclear'}  \n"
            f"**Bindingness:** {profile.get('bindingness', 'unclear')}"
        )
        for index, answer in enumerate(current.get("answers", []), start=1):
            with st.expander(
                f"{index}. {answer.get('question')} — {answer.get('answer')}",
                expanded=index == 1,
            ):
                confidence = float(answer.get("confidence", 0))
                st.caption(f"Provisional AI result · confidence {confidence:.0%}")
                st.write(answer.get("summary"))
                for evidence in answer.get("evidence", []):
                    st.markdown(f"> Page {evidence.get('page')}: “{evidence.get('quote')}”")
                if not answer.get("evidence"):
                    st.caption("No verified quotation was returned for this answer.")

workflow_navigation(
    previous=("Upload agreements", "pages/03_New_Document_Ingestion.py"),
    next_step=("Review findings", "pages/06_Adjudication.py"),
    note="Analyse a saved agreement, then review its nine provisional answers.",
    next_disabled=not bool(analyses),
)
