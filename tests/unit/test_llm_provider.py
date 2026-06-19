import pytest
import httpx

from app.llm.providers.openai_compatible import (
    ExternalLLMDisabledError,
    OpenAICompatibleProvider,
)
from app.llm.registry import build_provider, get_model_config, load_model_registry
from app.schemas.llm import LLMMessage, LLMRequest


def test_mock_llm_provider_returns_structured_output() -> None:
    registry = load_model_registry("config/models/model_registry.yaml")
    config = get_model_config(registry, "coding_model_v1")
    provider = build_provider(config)
    request = LLMRequest(
        model=config.model_name,
        temperature=config.temperature,
        messages=[
            LLMMessage(role="system", content="Return JSON."),
            LLMMessage(role="user", content="The Parties shall cooperate on critical minerals."),
        ],
    )

    response = provider.complete(request)

    assert response.provider == "mock"
    assert response.structured_output is not None
    assert response.structured_output["human_review_required"] is True
    assert response.structured_output["proposed_value"] == 1


def test_openai_provider_requires_explicit_external_llm_enablement() -> None:
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        allow_external_llm=False,
    )
    request = LLMRequest(
        model="gpt-4.1-mini",
        messages=[LLMMessage(role="user", content="Return JSON.")],
    )

    with pytest.raises(ExternalLLMDisabledError):
        provider.complete(request)


def test_openai_provider_parses_responses_api_json_without_real_network() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "output_text": (
                    '{"proposed_value": 1, "confidence": 0.82, '
                    '"evidence_quote": "shall cooperate", '
                    '"reasoning_summary": "Found mandatory language."}'
                ),
                "usage": {"input_tokens": 12, "output_tokens": 8},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        allow_external_llm=True,
        client=client,
    )
    request = LLMRequest(
        model="gpt-4.1-mini",
        temperature=0,
        messages=[LLMMessage(role="user", content="Return JSON.")],
    )

    response = provider.complete(request)

    assert response.provider == "openai_compatible"
    assert response.structured_output is not None
    assert response.structured_output["proposed_value"] == 1
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 8
