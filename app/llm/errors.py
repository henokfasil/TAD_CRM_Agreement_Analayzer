from __future__ import annotations


class ExternalLLMDisabledError(RuntimeError):
    """Raised when an external LLM call is requested without explicit approval."""


class ExternalLLMRequestError(RuntimeError):
    """Raised when an external LLM request fails after secrets have been validated."""
