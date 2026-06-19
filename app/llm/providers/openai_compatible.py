from __future__ import annotations

import json
from typing import Any

import httpx

from app.llm.errors import ExternalLLMDisabledError
from app.schemas.llm import LLMRequest, LLMResponse


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(
        self,
        api_key: str | None,
        base_url: str = "https://api.openai.com/v1",
        allow_external_llm: bool = False,
        client: httpx.Client | None = None,
        timeout: float = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.allow_external_llm = allow_external_llm
        self.client = client
        self.timeout = timeout

    def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.allow_external_llm:
            raise ExternalLLMDisabledError(
                "External LLM calls are disabled. Set ALLOW_EXTERNAL_LLM=true to use OpenAI."
            )
        if not self.api_key:
            raise ExternalLLMDisabledError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": request.model,
            "input": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "temperature": request.temperature,
        }
        client = self.client or httpx.Client(timeout=self.timeout)
        should_close_client = self.client is None
        try:
            response = client.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        finally:
            if should_close_client:
                client.close()

        content = _extract_response_text(data)
        usage = data.get("usage") or {}
        return LLMResponse(
            model=request.model,
            provider=self.provider_name,
            content=content,
            structured_output=_parse_json_object(content),
            prompt_tokens=int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0),
            completion_tokens=int(
                usage.get("output_tokens") or usage.get("completion_tokens") or 0
            ),
            cost_estimate=0,
        )


def _extract_response_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    fragments: list[str] = []
    for item in data.get("output") or []:
        for content in item.get("content") or []:
            text = content.get("text")
            if isinstance(text, str):
                fragments.append(text)
    return "\n".join(fragments)


def _parse_json_object(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None
