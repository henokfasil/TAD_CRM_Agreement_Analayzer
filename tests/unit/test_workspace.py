from pathlib import Path
import tempfile
from uuid import uuid4

from app.schemas.documents import ExtractedPage, ExtractionResult, StoredDocument
from app.services.ingestion.workspace import (
    build_document_record,
    clear_document_records,
    count_document_records,
    load_document_records,
    pages_to_csv,
    records_to_json,
    save_document_record,
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


def test_workspace_sqlite_roundtrip() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_workspace_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    stored = StoredDocument(
        original_filename="agreement.pdf",
        stored_path=runtime / "agreement.pdf",
        sha256_hash="abc123",
        size_bytes=123,
    )
    extraction = ExtractionResult(
        method="pymupdf",
        parser_version="1",
        pages=[ExtractedPage(page_number=1, text="First page")],
    )

    save_document_record(build_document_record(stored, extraction), db_path)

    assert count_document_records(db_path) == 1
    loaded = load_document_records(db_path)
    assert loaded[0]["original_filename"] == "agreement.pdf"
    assert loaded[0]["pages"][0]["text"] == "First page"

    clear_document_records(db_path)
    assert load_document_records(db_path) == []
