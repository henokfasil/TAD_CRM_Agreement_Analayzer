from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.codebook import CodebookSchema


def load_codebook(path: str | Path) -> CodebookSchema:
    resolved_path = Path(path)
    with resolved_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if "active_codebook_path" in payload:
        next_path = resolved_path.parent / payload["active_codebook_path"]
        return load_codebook(next_path)
    return CodebookSchema.model_validate(payload)
