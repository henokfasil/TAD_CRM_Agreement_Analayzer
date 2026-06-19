from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.services.ingestion.storage import store_upload
from app.services.parsing.pdf import extract_pdf_pages

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds configured upload limit.")

    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(content)
        temp_path = Path(handle.name)

    stored = store_upload(temp_path, settings.upload_dir, file.filename)
    extraction = None
    if stored.stored_path.suffix.lower() == ".pdf":
        extraction = extract_pdf_pages(stored.stored_path)

    return {
        "filename": stored.original_filename,
        "sha256_hash": stored.sha256_hash,
        "stored_path": str(stored.stored_path),
        "duplicate": stored.duplicate,
        "page_count": len(extraction.pages) if extraction else None,
        "extraction_method": extraction.method if extraction else None,
    }

