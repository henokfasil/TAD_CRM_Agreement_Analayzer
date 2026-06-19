from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from streamlit_app.bootstrap import ensure_project_root_on_path

ensure_project_root_on_path()

from app.core.config import get_settings
from app.core.exceptions import ExtractionError
from app.services.ingestion.storage import store_upload
from app.services.parsing.pdf import extract_pdf_pages

st.title("New Document Ingestion")
settings = get_settings()

tab_upload, tab_local = st.tabs(["Upload", "Local PDF"])


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
