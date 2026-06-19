from __future__ import annotations

from pathlib import Path

import yaml

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas.llm import ModelConfig, ModelRegistry


def load_model_registry(path: str | Path) -> ModelRegistry:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return ModelRegistry.model_validate(payload)


def get_model_config(registry: ModelRegistry, model_key: str) -> ModelConfig:
    return registry.models[model_key]


def resolve_runtime_model_config(config: ModelConfig) -> ModelConfig:
    if config.provider == "openai_compatible":
        settings = get_settings()
        if settings.openai_model:
            return config.model_copy(update={"model_name": settings.openai_model})
    return config


def build_provider(config: ModelConfig) -> LLMProvider:
    if config.provider == "mock":
        return MockLLMProvider()
    if config.provider == "openai_compatible":
        settings = get_settings()
        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            allow_external_llm=settings.allow_external_llm,
        )
    raise ValueError(f"Unsupported LLM provider: {config.provider}")
