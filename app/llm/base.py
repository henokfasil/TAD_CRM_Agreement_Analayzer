from __future__ import annotations

from typing import Protocol

from app.schemas.llm import LLMRequest, LLMResponse


class LLMProvider(Protocol):
    provider_name: str

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a provider response for a structured LLM request."""

