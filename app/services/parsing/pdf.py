from __future__ import annotations

from pathlib import Path

from app.core.exceptions import ExtractionError
from app.schemas.documents import ExtractedPage, ExtractionResult

MIN_USEFUL_TEXT_CHARS = 40


def _extract_native_text(page: object) -> str:
    return page.get_text("text").strip()


def _extract_ocr_text(page: object) -> str:
    """Run local Tesseract OCR through PyMuPDF for an image-based page."""
    text_page = page.get_textpage_ocr(language="eng", dpi=200, full=True)
    return page.get_text("text", textpage=text_page).strip()


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
    ocr_attempted = False
    ocr_page_count = 0
    ocr_warning: str | None = None
    try:
        for index, page in enumerate(document, start=1):
            text = _extract_native_text(page)
            if len(text) < MIN_USEFUL_TEXT_CHARS:
                ocr_attempted = True
                try:
                    ocr_text = _extract_ocr_text(page)
                except Exception:  # Tesseract may be absent in a local development environment.
                    ocr_warning = (
                        "Some pages contain little or no embedded text, and local OCR was not "
                        "available. Install Tesseract to process scanned PDFs."
                    )
                else:
                    if len(ocr_text) > len(text):
                        text = ocr_text
                        ocr_page_count += 1
            pages.append(ExtractedPage(page_number=index, text=text))
    finally:
        document.close()

    method = "pymupdf+ocr" if ocr_page_count else "pymupdf"
    return ExtractionResult(
        method=method,
        parser_version=getattr(fitz, "VersionBind", "unknown"),
        pages=pages,
        ocr_attempted=ocr_attempted,
        ocr_page_count=ocr_page_count,
        ocr_warning=ocr_warning,
    )
