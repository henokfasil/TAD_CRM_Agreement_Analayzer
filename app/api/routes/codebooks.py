from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.codebook import CodebookSchema
from app.services.codebook import load_codebook

router = APIRouter()


@router.get("/active", response_model=CodebookSchema)
def get_active_codebook() -> CodebookSchema:
    return load_codebook(get_settings().active_codebook_path)

