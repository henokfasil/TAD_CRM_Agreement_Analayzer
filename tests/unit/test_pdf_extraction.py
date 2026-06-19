from pathlib import Path
from uuid import uuid4

import pytest

from app.core.exceptions import ExtractionError
from app.services.parsing.pdf import extract_pdf_pages


def test_extract_pdf_pages_rejects_non_pdf() -> None:
    runtime = Path("data/fixtures/runtime") / str(uuid4())
    runtime.mkdir(parents=True, exist_ok=True)
    path = runtime / "not-a-pdf.pdf"
    path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ExtractionError):
        extract_pdf_pages(path)
