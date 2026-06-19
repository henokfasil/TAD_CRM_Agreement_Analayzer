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

st.title("New Document Ingestion")
settings = get_settings()

if "document_workspace" not in st.session_state:
    st.session_state.document_workspace = load_document_records()

tab_upload, tab_local, tab_workspace = st.tabs(["Upload", "Local PDF", "Workspace"])


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

    st.subheader("Page-Level Extraction")
    col_method, col_pages = st.columns(2)
    col_method.metric("Parser", extraction.method)
    col_pages.metric("Pages", len(extraction.pages))

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
            }
        )

    st.caption("This document is now available in the Workspace tab and Agreement Explorer.")


with tab_upload:
    uploaded = st.file_uploader("Upload agreement document", type=["pdf", "docx", "txt"])
    if uploaded:
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(uploaded.getbuffer())
            temp_path = Path(handle.name)
        render_extraction(temp_path, uploaded.name)

with tab_local:
    local_pdf = Path("CRM Agreements.pdf")
    if local_pdf.exists():
        st.write("Detected local project PDF.")
        st.code(str(local_pdf))
        if st.button("Extract local PDF", type="primary"):
            render_extraction(local_pdf, local_pdf.name)
    else:
        st.info("No `CRM Agreements.pdf` file found in the project root.")

with tab_workspace:
    records = load_document_records()
    st.session_state.document_workspace = records
    st.caption(
        "Workspace records are saved in a lightweight SQLite store for this app instance. "
        "Use downloads for durable research handoff until PostgreSQL is connected."
    )
    if not records:
        st.info("No documents have been extracted in this workspace yet.")
    else:
        st.metric("Documents in workspace", len(records))
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
        selected_page_number = st.selectbox("Workspace page", page_numbers)
        selected_page = next(
            page for page in selected["pages"] if page["page_number"] == selected_page_number
        )
        st.text_area("Workspace extracted text", selected_page["text"], height=320)

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
        if st.button("Clear workspace"):
            clear_document_records()
            st.session_state.document_workspace = []
            st.rerun()
