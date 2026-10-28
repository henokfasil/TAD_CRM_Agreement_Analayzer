from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.agreements.profiles import (  # noqa: E402
    load_agreement_document_links,
    load_agreement_profiles,
)
from app.services.ingestion.workspace import load_document_records  # noqa: E402
from app.services.research.readiness import build_research_readiness  # noqa: E402
from app.services.research.specification import load_report_specification  # noqa: E402
from app.services.review.adjudication import load_adjudication_decisions  # noqa: E402
from streamlit_app.ui import page_header, stat_cards  # noqa: E402


page_header(
    "Research engine",
    "Prepare a validated corpus that can generate reproducible figures, analysis, methods, and complete research reports.",
    eyebrow="Research production",
)

specification = load_report_specification()
profiles = load_agreement_profiles()
records = load_document_records()
links = load_agreement_document_links()
adjudications = load_adjudication_decisions()
readiness = build_research_readiness(
    profiles,
    records,
    links,
    adjudications,
    specification,
)

st.markdown(
    """
    <section class="crm-result-panel">
      <div class="crm-result-heading">
        <span class="crm-result-check">R</span>
        <div><div class="crm-result-kicker">End goal</div>
        <h3>Validate once. Reproduce and update research in seconds.</h3></div>
        <span class="crm-status-pill">Foundation</span>
      </div>
      <p style="margin:1rem 0 0;color:var(--crm-muted)">
        The original paper defines the expected standard of output. Its figures are not copied here.
        The engine is being organised so future figures and reports are computed from the live,
        evidence-linked corpus.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)

stat_cards(
    [
        ("Saved documents", readiness["documents"], "Original PDFs and extracted pages"),
        ("Agreement profiles", readiness["agreement_profiles"], "Structured research records"),
        ("Core metadata ready", readiness["core_metadata_complete"], "Profiles complete for analysis"),
        ("Validated profiles", readiness["validated_profiles"], "Eligible for final publication"),
    ]
)

if readiness["publication_ready"]:
    st.success(
        "The current included corpus has complete and validated core metadata.",
        icon=":material/check_circle:",
    )
else:
    st.warning(
        "The engine is available for corpus preparation, but the current corpus is not yet "
        "publication-ready. Complete and validate agreement profiles before final reporting.",
        icon=":material/pending_actions:",
    )

tab_readiness, tab_registry, tab_report, tab_method = st.tabs(
    ["Corpus readiness", "Analysis registry", "Future report", "Methods contract"]
)

with tab_readiness:
    st.subheader("Readiness by analytical family")
    st.caption(
        "This is a quality-control view, not a reproduction of the paper's figures. "
        "Exploratory analyses may use complete provisional records; publication requires validation."
    )
    st.dataframe(
        readiness["analysis_rows"],
        hide_index=True,
        column_config={
            "analysis_id": None,
            "required_fields": st.column_config.TextColumn("Required research fields", width="large"),
            "complete_records": st.column_config.NumberColumn("Complete"),
            "validated_records": st.column_config.NumberColumn("Validated"),
            "corpus_records": st.column_config.NumberColumn("Corpus"),
            "readiness": st.column_config.TextColumn("Output status"),
            "implementation": st.column_config.TextColumn("Engine stage"),
        },
    )
    st.caption(
        f"Research contract: {readiness['specification_version']} · "
        f"Linked profiles: {readiness['linked_profiles']} · "
        f"Final decisions: {readiness['adjudicated_decisions']}"
    )

with tab_registry:
    st.subheader("Versioned analysis registry")
    st.caption(
        "Each future output receives a stable definition covering its population, required fields, "
        "validation rules, calculation, underlying data, and limitations."
    )
    registry_rows = [
        {
            "Reference": item.get("reference"),
            "Analytical output": item.get("title"),
            "Research purpose": item.get("purpose"),
            "Required fields": ", ".join(item.get("required_fields", [])),
            "Stage": item.get("status"),
        }
        for item in specification["analysis_registry"]
    ]
    st.dataframe(
        registry_rows,
        hide_index=True,
        column_config={
            "Research purpose": st.column_config.TextColumn(width="large"),
            "Required fields": st.column_config.TextColumn(width="large"),
        },
    )

with tab_report:
    st.subheader("Target research-report package")
    st.caption(
        "Report generation will be enabled after the analytical contracts and validation gates are implemented."
    )
    output_column, section_column = st.columns(2)
    with output_column:
        with st.container(border=True):
            st.markdown("#### Publication formats")
            for output in specification.get("outputs", []):
                st.markdown(f":material/check_circle: {output}")
    with section_column:
        with st.container(border=True):
            st.markdown("#### Report structure")
            for index, section in enumerate(specification.get("report_sections", []), start=1):
                st.markdown(f"{index}. {section}")
    st.info(
        "The future generator will offer baseline, live-corpus, and custom-report modes. "
        "It will never silently mix provisional and validated results.",
        icon=":material/article:",
    )

with tab_method:
    st.subheader("Publication safeguards")
    safeguards = specification.get("publication_rules", {})
    safeguards_rows = [
        {
            "Rule": key.replace("_", " ").title(),
            "Requirement": (
                "Required" if value is True else "Not required" if value is False else str(value)
            ),
        }
        for key, value in safeguards.items()
    ]
    st.dataframe(safeguards_rows, hide_index=True)
    st.markdown(
        """
        #### Research-production principle

        Document processing can be slow once. Report generation must be fast many times.
        Deterministic code calculates official indicators; language models may explain validated
        outputs but may not invent figures, alter denominators, or publish unsupported claims.
        """
    )
