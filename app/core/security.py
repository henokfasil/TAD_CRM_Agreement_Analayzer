from __future__ import annotations

from pathlib import Path


def safe_filename(filename: str) -> str:
    cleaned = Path(filename).name.replace("\x00", "")
    return cleaned or "uploaded_document"

