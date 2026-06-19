from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion.workspace import load_document_records, pages_to_csv, records_to_json

st.title("Agreement Explorer")
records = load_document_records()
st.session_state.document_workspace = records
st.caption(
    "This explorer reads from the prototype SQLite document workspace. "
    "Validated agreement records will move to PostgreSQL in a later phase."
)

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

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Pages", selected["page_count"])
    col_b.metric("Parser", selected["extraction_method"] or "n/a")
    col_c.metric("SHA-256", selected["sha256_hash"][:12])

    page_numbers = [page["page_number"] for page in selected["pages"]]
    selected_page_number = st.selectbox("Page", page_numbers)
    selected_page = next(
        page for page in selected["pages"] if page["page_number"] == selected_page_number
    )
    st.text_area("Extracted page text", selected_page["text"], height=420)

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
