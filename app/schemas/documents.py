from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class StoredDocument(BaseModel):
    original_filename: str
    stored_path: Path
    sha256_hash: str
    size_bytes: int
    duplicate: bool = False


class ExtractedPage(BaseModel):
    page_number: int
    text: str
    extraction_confidence: float | None = None


class ExtractionResult(BaseModel):
    method: str
    parser_version: str
    pages: list[ExtractedPage]

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

