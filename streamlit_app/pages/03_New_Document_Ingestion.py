from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.exceptions import ExtractionError
from app.services.ingestion.storage import store_upload
from app.services.ingestion.workspace import (
    build_document_record,
    clear_document_records,
    load_document_records,
    pages_to_csv,
    records_to_json,
    save_document_record,
    upsert_document_record,
)
from app.services.parsing.pdf import extract_pdf_pages
from app.services.segmentation.basic import segment_document_pages
from streamlit_app.runtime_config import sync_streamlit_secrets_to_env
from streamlit_app.ui import page_header, workflow_navigation

page_header(
    "Upload agreements",
    "Add PDF agreements, recover scanned text with OCR, and confirm that the text is readable.",
    eyebrow="Step 2 of 6",
)
sync_streamlit_secrets_to_env()
settings = get_settings()

if "document_workspace" not in st.session_state:
    st.session_state.document_workspace = load_document_records()

tab_upload, tab_saved = st.tabs(["Upload agreement", "Saved agreements"])


def render_extraction(path: Path, original_filename: str | None = None) -> None:
    stored = store_upload(path, settings.upload_dir, original_filename)
    st.success("Document stored and fingerprinted.")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Size", f"{stored.size_bytes / 1024:,.1f} KB")
    col_b.metric("Duplicate", "Yes" if stored.duplicate else "No")
    col_c.metric("SHA-256", stored.sha256_hash[:12])

    if stored.stored_path.suffix.lower() != ".pdf":
        st.warning("Only PDF extraction is implemented in Phase 1.")
        return

    try:
        extraction = extract_pdf_pages(stored.stored_path)
    except ExtractionError as exc:
        st.error(str(exc))
        return

    record = build_document_record(stored, extraction)
    save_document_record(record)
    st.session_state.document_workspace = upsert_document_record(
        load_document_records(),
        record,
    )

    text_pages = sum(bool(page.text.strip()) for page in extraction.pages)
    text_characters = sum(len(page.text.strip()) for page in extraction.pages)
    provisions = segment_document_pages(record)

    st.subheader("Extraction results")
    col_method, col_pages, col_text, col_provisions = st.columns(4)
    col_method.metric("Parser", extraction.method)
    col_pages.metric("Pages", len(extraction.pages))
    col_text.metric("Pages with text", f"{text_pages}/{len(extraction.pages)}")
    col_provisions.metric("Candidate provisions", len(provisions))

    if extraction.ocr_page_count:
        st.success(
            f"OCR recovered text from {extraction.ocr_page_count} scanned "
            f"page{'s' if extraction.ocr_page_count != 1 else ''}."
        )
    if extraction.ocr_warning:
        st.warning(extraction.ocr_warning)
    if not text_characters:
        st.error(
            "No readable text was extracted. This document cannot proceed to classification yet. "
            "Try an OCR-readable copy or ask an administrator to verify Tesseract installation."
        )
    elif not provisions:
        st.warning(
            "Text was extracted, but no candidate provisions were detected. Review the extracted "
            "pages before continuing."
        )
    else:
        st.success(
            "The document is ready. Review its pages and candidate provisions, then continue to "
            "classification and verification."
        )

    page_numbers = [page.page_number for page in extraction.pages]
    selected_page_number = st.selectbox("Page", page_numbers)
    selected_page = next(page for page in extraction.pages if page.page_number == selected_page_number)
    st.text_area(
        "Extracted text",
        value=selected_page.text,
        height=360,
        label_visibility="collapsed",
    )

    with st.expander("Document provenance"):
        st.json(
            {
                "original_filename": stored.original_filename,
                "stored_path": str(stored.stored_path),
                "sha256_hash": stored.sha256_hash,
                "parser_version": extraction.parser_version,
                "page_count": len(extraction.pages),
                "ocr_attempted": extraction.ocr_attempted,
                "ocr_page_count": extraction.ocr_page_count,
            }
        )

with tab_upload:
    st.caption("Choose a PDF. The original file and its extracted text are saved for later sessions.")
    uploaded = st.file_uploader("Choose an agreement PDF", type=["pdf"])
    if uploaded:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(uploaded.getbuffer())
            temp_path = Path(handle.name)
        try:
            render_extraction(temp_path, uploaded.name)
        finally:
            temp_path.unlink(missing_ok=True)

with tab_saved:
    records = load_document_records()
    st.session_state.document_workspace = records
    st.caption(
        "Uploaded agreements and extracted text are saved securely and remain available across sessions."
    )
    if not records:
        st.info("No saved agreements yet. Upload the first PDF in the tab above.")
    else:
        st.metric("Saved agreements", len(records))
        st.dataframe(
            [
                {
                    "filename": record["original_filename"],
                    "pages": record["page_count"],
                    "sha256": record["sha256_hash"][:12],
                    "parser": record["extraction_method"],
                }
                for record in records
            ],
            use_container_width=True,
            hide_index=True,
        )

        selected_id = st.selectbox(
            "Document",
            [record["document_id"] for record in records],
            format_func=lambda value: next(
                record["original_filename"] for record in records if record["document_id"] == value
            ),
        )
        selected = next(record for record in records if record["document_id"] == selected_id)
        page_numbers = [page["page_number"] for page in selected["pages"]]
        selected_page_number = st.selectbox("Page", page_numbers)
        selected_page = next(
            page for page in selected["pages"] if page["page_number"] == selected_page_number
        )
        st.text_area("Extracted text", selected_page["text"], height=320)

        col_json, col_csv = st.columns(2)
        col_json.download_button(
            "Download agreement records JSON",
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
        st.warning("Deleting removes every saved agreement and its extracted text from the app.")
        confirm_delete = st.checkbox("I understand that all saved agreements will be deleted")
        if st.button("Delete all saved agreements", disabled=not confirm_delete):
            clear_document_records()
            st.session_state.document_workspace = []
            st.rerun()

records = load_document_records()
workflow_navigation(
    previous=("Discover agreements", "pages/04_Discovery_Queue.py"),
    next_step=("Review & structure", "pages/02_Agreement_Explorer.py"),
    note=(
        "Your extracted agreement is ready for review."
        if records
        else "Upload and extract at least one agreement before continuing."
    ),
    next_disabled=not records,
)
