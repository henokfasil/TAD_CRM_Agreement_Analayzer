from __future__ import annotations

from pathlib import Path

import yaml

from app.llm.base import LLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.schemas.llm import ModelConfig, ModelRegistry


def load_model_registry(path: str | Path) -> ModelRegistry:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return ModelRegistry.model_validate(payload)


def get_model_config(registry: ModelRegistry, model_key: str) -> ModelConfig:
    return registry.models[model_key]


def build_provider(config: ModelConfig) -> LLMProvider:
    if config.provider == "mock":
        return MockLLMProvider()
    raise ValueError(f"Unsupported LLM provider: {config.provider}")

