from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CRM Agreement Intelligence System"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://crm:crm@localhost:5432/crm_agreements"
    upload_dir: Path = Path("data/raw/uploads")
    max_upload_mb: int = Field(default=50, gt=0)
    active_codebook_path: Path = Path("config/codebooks/active_codebook.yaml")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

