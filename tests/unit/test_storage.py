from pathlib import Path
from uuid import uuid4

from app.services.ingestion.storage import sha256_file, store_upload


def test_store_upload_detects_duplicate() -> None:
    runtime = Path("data/fixtures/runtime") / str(uuid4())
    runtime.mkdir(parents=True, exist_ok=True)
    source = runtime / "doc.txt"
    source.write_text("same content", encoding="utf-8")
    upload_dir = runtime / "uploads"

    first = store_upload(source, upload_dir)
    second = store_upload(source, upload_dir)

    assert first.sha256_hash == sha256_file(source)
    assert first.duplicate is False
    assert second.duplicate is True
