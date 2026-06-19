from __future__ import annotations

import json

from app.schemas.llm import LLMRequest, LLMResponse


class MockLLMProvider:
    provider_name = "mock"

    def complete(self, request: LLMRequest) -> LLMResponse:
        text = "\n".join(message.content for message in request.messages)
        proposed_value = 1 if any(term in text.lower() for term in ["shall", "critical", "crm"]) else 0
        structured = {
            "proposed_value": proposed_value,
            "confidence": 0.5,
            "evidence_quote": text[:240],
            "reasoning_summary": "Deterministic mock output for prototype wiring only.",
            "human_review_required": True,
        }
        return LLMResponse(
            model=request.model,
            provider=self.provider_name,
            content=json.dumps(structured),
            structured_output=structured,
            prompt_tokens=sum(len(message.content.split()) for message in request.messages),
            completion_tokens=len(json.dumps(structured).split()),
            cost_estimate=0,
        )

