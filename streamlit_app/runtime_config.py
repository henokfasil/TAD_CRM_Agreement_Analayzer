from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


SECRET_ENV_KEYS = {
    "ALLOW_EXTERNAL_LLM",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "GEMINI_API_KEY",
    "GEMINI_BASE_URL",
    "GEMINI_MODEL",
}

OPENAI_SECRET_MAP = {
    "api_key": "OPENAI_API_KEY",
    "base_url": "OPENAI_BASE_URL",
    "model": "OPENAI_MODEL",
    "allow_external_llm": "ALLOW_EXTERNAL_LLM",
}

GEMINI_SECRET_MAP = {
    "api_key": "GEMINI_API_KEY",
    "base_url": "GEMINI_BASE_URL",
    "model": "GEMINI_MODEL",
    "allow_external_llm": "ALLOW_EXTERNAL_LLM",
}


def sync_streamlit_secrets_to_env() -> None:
    try:
        secrets = st.secrets
        openai_secrets = secrets.get("openai", {})
        gemini_secrets = secrets.get("gemini", {})
    except StreamlitSecretNotFoundError:
        return

    for key in SECRET_ENV_KEYS:
        _set_env_if_present(key, secrets)

    if isinstance(openai_secrets, Mapping):
        for secret_key, env_key in OPENAI_SECRET_MAP.items():
            _set_env_if_present(env_key, openai_secrets, secret_key)

    if isinstance(gemini_secrets, Mapping):
        for secret_key, env_key in GEMINI_SECRET_MAP.items():
            _set_env_if_present(env_key, gemini_secrets, secret_key)


def _set_env_if_present(
    env_key: str,
    source: Mapping[str, Any],
    source_key: str | None = None,
) -> None:
    if os.environ.get(env_key):
        return
    value = source.get(source_key or env_key)
    if value is not None:
        os.environ[env_key] = str(value)
