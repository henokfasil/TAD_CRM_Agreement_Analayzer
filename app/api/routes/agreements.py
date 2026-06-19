from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_agreements() -> dict[str, list]:
    return {"agreements": []}

