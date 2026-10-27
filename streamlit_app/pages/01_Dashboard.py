from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion.workspace import load_document_records
from app.services.reporting.exports import build_candidate_provisions, build_workspace_summary
from app.services.review.manual_coding import load_manual_decisions
from app.services.agreements.profiles import load_agreement_profiles
from app.services.classification.ai_coding import load_ai_coding_proposals
from app.services.review.adjudication import load_adjudication_decisions
from app.services.verification.ai_verification import load_verification_results
from streamlit_app.ui import bar_panel, page_header, stat_cards

page_header(
    "Research dashboard",
    "See what has been collected, what still needs review, and how much validated evidence is ready.",
    eyebrow="Workspace overview",
)
records = load_document_records()
decisions = load_manual_decisions()
profiles = load_agreement_profiles()
ai_proposals = load_ai_coding_proposals()
verification_results = load_verification_results()
adjudications = load_adjudication_decisions()
summary = build_workspace_summary(records, decisions, profiles, ai_proposals, verification_results, adjudications)

st.markdown(
    '<div class="crm-dashboard-section"><h2>Workspace at a glance</h2>'
    '<p>A compact view of document volume and evidence preparation.</p></div>',
    unsafe_allow_html=True,
)
stat_cards(
    [
        ("Saved agreements", summary["documents"], "Original PDFs and extracted text"),
        ("Pages processed", summary["pages"], "Across all saved agreements"),
        ("Candidate provisions", summary["candidate_provisions"], "Passages available for classification"),
        ("Final decisions", summary["adjudicated_decisions"], "Human-reviewed research results"),
    ]
)

st.markdown(
    '<div class="crm-dashboard-section"><h2>Review pipeline</h2>'
    '<p>These counts show movement from initial classification to a final human decision.</p></div>',
    unsafe_allow_html=True,
)
stat_cards(
    [
        ("Manual classifications", summary["manual_coding_decisions"], "Values entered by reviewers"),
        ("AI suggestions", summary["ai_coding_proposals"], "Provisional, never automatically final"),
        ("Verification checks", summary["verification_results"], "Evidence and consistency checks"),
        ("Agreement profiles", summary["agreement_profiles"], "Structured agreement-level records"),
    ]
)

if not records:
    st.info("Upload and extract an agreement to begin populating this dashboard.")
elif not decisions:
    st.info("Your documents are ready. Classify a provision in Step 4 to begin the review charts.")

chart_left = bar_panel(
    "Reviewer status",
    "How saved classifications are progressing.",
    summary["reviewer_status_counts"],
)
chart_right = bar_panel(
    "Classified variables",
    "Research variables represented in reviewer decisions.",
    summary["coded_variable_counts"],
)
st.markdown(f'<div class="crm-bar-grid">{chart_left}{chart_right}</div>', unsafe_allow_html=True)

with st.expander("Preview candidate provisions"):
    provisions = build_candidate_provisions(records)
    if provisions:
        st.dataframe(
            [
                {
                    "page": provision["page_start"],
                    "method": provision["segmentation_method"],
                    "text": provision["provision_text"][:180],
                }
                for provision in provisions[:25]
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.write("No candidate provisions available.")
