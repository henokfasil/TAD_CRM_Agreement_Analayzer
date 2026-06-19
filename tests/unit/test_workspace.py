from pathlib import Path

from app.schemas.documents import ExtractedPage, ExtractionResult, StoredDocument
from app.services.ingestion.workspace import (
    build_document_record,
    pages_to_csv,
    records_to_json,
    upsert_document_record,
)


def test_workspace_record_exports() -> None:
    stored = StoredDocument(
        original_filename="agreement.pdf",
        stored_path=Path("data/raw/uploads/example.pdf"),
        sha256_hash="abc123",
        size_bytes=123,
    )
    extraction = ExtractionResult(
        method="pymupdf",
        parser_version="1",
        pages=[ExtractedPage(page_number=1, text="First page")],
    )

    record = build_document_record(stored, extraction)
    records = upsert_document_record([], record)

    assert records[0]["document_id"] == "abc123"
    assert "First page" in records_to_json(records)
    assert "agreement.pdf" in pages_to_csv(records)
