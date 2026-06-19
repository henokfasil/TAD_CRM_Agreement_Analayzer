from __future__ import annotations


class ExternalLLMDisabledError(RuntimeError):
    """Raised when an external LLM call is requested without explicit approval."""
