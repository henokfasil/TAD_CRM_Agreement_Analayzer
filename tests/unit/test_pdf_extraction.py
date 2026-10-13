from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ExtractionError
from app.services.parsing.pdf import extract_pdf_pages
from app.services.parsing.pdf import MIN_USEFUL_TEXT_CHARS, _extract_ocr_text


def test_extract_pdf_pages_rejects_non_pdf() -> None:
    runtime = Path("data/fixtures/runtime") / str(uuid4())
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / "not-a-pdf.pdf"
    path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ExtractionError):
        extract_pdf_pages(path)


def test_ocr_text_uses_pymupdf_text_page() -> None:
    class FakePage:
        def get_textpage_ocr(self, **kwargs):
            assert kwargs == {"language": "eng", "dpi": 200, "full": True}
            return "ocr-text-page"

        def get_text(self, kind, **kwargs):
            assert kind == "text"
            assert kwargs == {"textpage": "ocr-text-page"}
            return "  OCR agreement text  "

    assert _extract_ocr_text(FakePage()) == "OCR agreement text"
    assert MIN_USEFUL_TEXT_CHARS > 0


def test_extract_pdf_pages_falls_back_to_ocr(monkeypatch) -> None:
    class FakePage:
        def get_textpage_ocr(self, **kwargs):
            return "ocr-text-page"

        def get_text(self, kind, **kwargs):
            if kwargs.get("textpage") == "ocr-text-page":
                return "Recovered agreement text from a scanned page using local OCR."
            return ""

    class FakeDocument(list):
        def close(self):
            return None

    fake_fitz = SimpleNamespace(
        VersionBind="test-version",
        open=lambda path: FakeDocument([FakePage()]),
    )
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    result = extract_pdf_pages(Path("scanned.pdf"))

    assert result.method == "pymupdf+ocr"
    assert result.ocr_attempted is True
    assert result.ocr_page_count == 1
    assert result.pages[0].text.startswith("Recovered agreement text")
