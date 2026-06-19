from __future__ import annotations

from pathlib import Path

from app.core.exceptions import ExtractionError
from app.schemas.documents import ExtractedPage, ExtractionResult


def extract_pdf_pages(path: Path) -> ExtractionResult:
    try:
        import fitz
    except ImportError as exc:
        raise ExtractionError("PyMuPDF is required for PDF extraction.") from exc

    try:
        document = fitz.open(path)
    except Exception as exc:  # pragma: no cover - library-specific parse failures
        raise ExtractionError(f"Could not open PDF: {path}") from exc

    pages: list[ExtractedPage] = []
    try:
        for index, page in enumerate(document, start=1):
            pages.append(ExtractedPage(page_number=index, text=page.get_text("text").strip()))
    finally:
        document.close()

    return ExtractionResult(method="pymupdf", parser_version=getattr(fitz, "VersionBind", "unknown"), pages=pages)

