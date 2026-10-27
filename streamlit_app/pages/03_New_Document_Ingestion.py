from __future__ import annotations

import sys
import tempfile
from html import escape
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

    filename = escape(stored.original_filename)
    is_readable = bool(text_characters)
    if is_readable:
        result_title = "Agreement ready"
        result_icon = "✓"
        result_status = "Already saved" if stored.duplicate else "New agreement"
        result_modifier = ""
    else:
        result_title = "File saved — text needs attention"
        result_icon = "!"
        result_status = "OCR needed"
        result_modifier = " crm-result-panel--warning"
    ocr_note = (
        f"OCR read {extraction.ocr_page_count} scanned page"
        f"{'s' if extraction.ocr_page_count != 1 else ''}"
        if extraction.ocr_page_count
        else ("Digital text detected" if is_readable else "No text recovered")
    )
    st.markdown(
        f"""
        <section class="crm-result-panel{result_modifier}">
            <div class="crm-result-heading">
                <span class="crm-result-check">{result_icon}</span>
                <div><div class="crm-result-kicker">{escape(result_title)}</div><h3>{filename}</h3></div>
                <span class="crm-status-pill">{escape(result_status)}</span>
            </div>
            <div class="crm-summary-grid">
                <div><span>Pages</span><strong>{len(extraction.pages)}</strong></div>
                <div><span>Readable</span><strong>{text_pages} of {len(extraction.pages)}</strong></div>
                <div><span>Provisions found</span><strong>{len(provisions)}</strong></div>
                <div><span>Text recovery</span><strong>{escape(ocr_note)}</strong></div>
                <div><span>File size</span><strong>{stored.size_bytes / 1024:,.0f} KB</strong></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not text_characters:
        st.warning(
            "The PDF is safely stored, but its pages contain no readable embedded text. "
            "OCR is needed before analysis can continue. Ask an administrator to enable Tesseract "
            "or upload a searchable PDF."
        )
    elif extraction.ocr_warning:
        st.warning(extraction.ocr_warning)
    elif not provisions:
        st.warning(
            "Text was extracted, but no candidate provisions were detected. Review the extracted "
            "pages before continuing."
        )
    else:
        st.caption(
            "Review the extracted text below. When it looks correct, continue to Review & structure."
        )

    if text_characters:
        st.markdown('<div class="crm-preview-title">Preview extracted text</div>', unsafe_allow_html=True)
        page_numbers = [page.page_number for page in extraction.pages]
        page_column, detail_column = st.columns([1, 4], vertical_alignment="bottom")
        with page_column:
            selected_page_number = st.selectbox("Page", page_numbers, key="uploaded_document_page")
        with detail_column:
            st.caption(f"Extracted with {extraction.method} · source fingerprint {stored.sha256_hash[:12]}")
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
        selected_page_number = st.selectbox("Page", page_numbers, key="saved_document_page")
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
        confirm_delete = st.checkbox(
            "I understand that all saved agreements will be deleted",
            key="confirm_delete_saved_agreements",
        )
        if st.button("Delete all saved agreements", disabled=not confirm_delete):
            clear_document_records()
            st.session_state.document_workspace = []
            st.rerun()

records = load_document_records()
has_readable_agreement = any(
    any(str(page.get("text", "")).strip() for page in record.get("pages", []))
    for record in records
)
workflow_navigation(
    previous=("Discover agreements", "pages/04_Discovery_Queue.py"),
    next_step=("Review & structure", "pages/02_Agreement_Explorer.py"),
    note=(
        "At least one saved agreement has readable text and is ready for review."
        if has_readable_agreement
        else (
            "Files are saved, but readable text is still needed before review."
            if records
            else "Upload and extract at least one agreement before continuing."
        )
    ),
    next_disabled=not has_readable_agreement,
)
