from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.agreements.profiles import (
    agreement_profiles_to_csv,
    build_agreement_profile,
    link_document_to_agreement,
    load_agreement_document_links,
    load_agreement_profiles,
    save_agreement_profile,
)
from app.services.ingestion.workspace import load_document_records, pages_to_csv, records_to_json
from app.services.segmentation.basic import segment_document_pages, provisions_to_csv

st.title("Agreement Explorer")
records = load_document_records()
profiles = load_agreement_profiles()
links = load_agreement_document_links()
st.session_state.document_workspace = records
st.caption(
    "This explorer reads from the prototype SQLite workspace. "
    "Validated agreement records will move to PostgreSQL in a later phase."
)

tab_profiles, tab_documents = st.tabs(["Agreement Profiles", "Documents and Provisions"])

with tab_profiles:
    st.subheader("Create Agreement Profile")
    with st.form("agreement_profile_form"):
        canonical_title = st.text_input("Canonical title")
        short_title = st.text_input("Short title")
        agreement_type = st.selectbox(
            "Agreement type",
            ["", "MoU", "partnership", "cooperation agreement", "trade agreement", "other"],
        )
        parties = st.text_input("Parties / countries")
        signature_date = st.text_input("Signature date")
        source_language = st.text_input("Source language", value="English")
        inclusion_status = st.selectbox("Inclusion status", ["pending", "included", "excluded", "uncertain"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save agreement profile")

    if submitted:
        if canonical_title.strip():
            save_agreement_profile(
                build_agreement_profile(
                    canonical_title=canonical_title,
                    short_title=short_title,
                    agreement_type=agreement_type,
                    parties=parties,
                    signature_date=signature_date,
                    source_language=source_language,
                    inclusion_status=inclusion_status,
                    notes=notes,
                )
            )
            st.success("Agreement profile saved.")
            st.rerun()
        else:
            st.error("Canonical title is required.")

    if profiles:
        st.subheader("Saved Profiles")
        st.dataframe(profiles, use_container_width=True, hide_index=True)
        st.download_button(
            "Download agreement profiles CSV",
            agreement_profiles_to_csv(profiles),
            file_name="crm_agreement_profiles.csv",
            mime="text/csv",
        )
    else:
        st.info("No agreement profiles saved yet.")

with tab_documents:
    if not records:
        st.info("No extracted documents in the workspace. Use New Document Ingestion first.")
    else:
        st.metric("Extracted documents", len(records))
        selected_id = st.selectbox(
            "Document",
            [record["document_id"] for record in records],
            format_func=lambda value: next(
                record["original_filename"] for record in records if record["document_id"] == value
            ),
        )
        selected = next(record for record in records if record["document_id"] == selected_id)

        if profiles:
            profile_options = [""] + [profile["agreement_id"] for profile in profiles]
            current_link = next(
                (link for link in links if link["document_id"] == selected["document_id"]),
                None,
            )
            default_index = (
                profile_options.index(current_link["agreement_id"])
                if current_link and current_link["agreement_id"] in profile_options
                else 0
            )
            selected_agreement_id = st.selectbox(
                "Linked agreement profile",
                profile_options,
                index=default_index,
                format_func=lambda value: "Unlinked"
                if not value
                else next(
                    profile["canonical_title"] for profile in profiles if profile["agreement_id"] == value
                ),
            )
            if selected_agreement_id and st.button("Link document to agreement"):
                link_document_to_agreement(selected_agreement_id, selected["document_id"])
                st.success("Document linked to agreement profile.")
                st.rerun()
        else:
            st.info("Create an agreement profile to link this document.")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Pages", selected["page_count"])
        col_b.metric("Parser", selected["extraction_method"] or "n/a")
        col_c.metric("SHA-256", selected["sha256_hash"][:12])

        tab_pages, tab_provisions = st.tabs(["Pages", "Candidate Provisions"])

        with tab_pages:
            page_numbers = [page["page_number"] for page in selected["pages"]]
            selected_page_number = st.selectbox("Page", page_numbers)
            selected_page = next(
                page for page in selected["pages"] if page["page_number"] == selected_page_number
            )
            st.text_area("Extracted page text", selected_page["text"], height=420)

        with tab_provisions:
            provisions = segment_document_pages(selected)
            st.metric("Candidate provisions", len(provisions))
            st.caption(
                "These are heuristic segments for review and downstream coding. "
                "They are not validated legal provisions."
            )
            if provisions:
                selected_provision_id = st.selectbox(
                    "Candidate provision",
                    [provision["provision_id"] for provision in provisions],
                    format_func=lambda value: next(
                        f"Page {provision['page_start']} | "
                        f"{provision['section_title'] or provision['segmentation_method']} | "
                        f"{provision['provision_text'][:70]}"
                        for provision in provisions
                        if provision["provision_id"] == value
                    ),
                )
                selected_provision = next(
                    provision
                    for provision in provisions
                    if provision["provision_id"] == selected_provision_id
                )
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Page", selected_provision["page_start"])
                col_p2.metric("Method", selected_provision["segmentation_method"])
                col_p3.metric("Version", selected_provision["segmentation_version"])
                st.text_area(
                    "Candidate provision text",
                    selected_provision["provision_text"],
                    height=360,
                )
                st.download_button(
                    "Download candidate provisions CSV",
                    provisions_to_csv(provisions),
                    file_name="crm_candidate_provisions.csv",
                    mime="text/csv",
                )
            else:
                st.info("No candidate provisions were detected for this document.")

        with st.expander("Document provenance"):
            st.json(
                {
                    "original_filename": selected["original_filename"],
                    "sha256_hash": selected["sha256_hash"],
                    "stored_path": selected["stored_path"],
                    "created_at": selected["created_at"],
                    "parser_version": selected["parser_version"],
                }
            )

        col_json, col_csv = st.columns(2)
        col_json.download_button(
            "Download workspace JSON",
            records_to_json(records),
            file_name="crm_document_workspace.json",
            mime="application/json",
        )
        col_csv.download_button(
            "Download extracted pages CSV",
            pages_to_csv(records),
            file_name="crm_extracted_pages.csv",
            mime="text/csv",
        )
