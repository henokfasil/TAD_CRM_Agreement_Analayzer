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
