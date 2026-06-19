from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import agreements, codebooks, documents, system
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(system.router)
    app.include_router(agreements.router, prefix="/agreements", tags=["agreements"])
    app.include_router(documents.router, prefix="/documents", tags=["documents"])
    app.include_router(codebooks.router, prefix="/codebooks", tags=["codebooks"])
    return app


app = create_app()

