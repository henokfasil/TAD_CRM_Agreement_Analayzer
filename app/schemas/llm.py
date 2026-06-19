from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str
    temperature: float = 0
    response_format: Literal["json", "text"] = "json"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    model: str
    provider: str
    content: str
    structured_output: dict[str, Any] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_estimate: float = 0


class ModelConfig(BaseModel):
    provider: str
    model_name: str
    temperature: float = 0
    purpose: str


class ModelRegistry(BaseModel):
    models: dict[str, ModelConfig]

