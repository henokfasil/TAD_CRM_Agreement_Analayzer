from __future__ import annotations

import json
from typing import Any

import httpx

from app.llm.errors import ExternalLLMDisabledError
from app.schemas.llm import LLMMessage, LLMRequest, LLMResponse


class GeminiProvider:
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
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
                "External LLM calls are disabled. Set ALLOW_EXTERNAL_LLM=true to use Gemini."
            )
        if not self.api_key:
            raise ExternalLLMDisabledError("GEMINI_API_KEY is not configured.")

        payload = _build_payload(request)
        client = self.client or httpx.Client(timeout=self.timeout)
        should_close_client = self.client is None
        try:
            response = client.post(
                f"{self.base_url}/models/{request.model}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        finally:
            if should_close_client:
                client.close()

        content = _extract_response_text(data)
        usage = data.get("usageMetadata") or {}
        return LLMResponse(
            model=request.model,
            provider=self.provider_name,
            content=content,
            structured_output=_parse_json_object(content),
            prompt_tokens=int(usage.get("promptTokenCount") or 0),
            completion_tokens=int(usage.get("candidatesTokenCount") or 0),
            cost_estimate=0,
        )


def _build_payload(request: LLMRequest) -> dict[str, Any]:
    system_text = "\n".join(
        message.content for message in request.messages if message.role == "system"
    )
    payload: dict[str, Any] = {
        "contents": [_to_gemini_content(message) for message in request.messages if message.role != "system"],
        "generationConfig": {"temperature": request.temperature},
    }
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}
    if request.response_format == "json":
        payload["generationConfig"]["responseMimeType"] = "application/json"
    return payload


def _to_gemini_content(message: LLMMessage) -> dict[str, Any]:
    role = "model" if message.role == "assistant" else "user"
    return {"role": role, "parts": [{"text": message.content}]}


def _extract_response_text(data: dict[str, Any]) -> str:
    fragments: list[str] = []
    for candidate in data.get("candidates") or []:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            text = part.get("text")
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
