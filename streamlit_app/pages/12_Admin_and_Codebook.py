from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.llm.registry import load_model_registry, resolve_runtime_model_config
from app.services.codebook import load_codebook
from app.services.storage.schema import get_schema_status, initialize_application_schema
from streamlit_app.runtime_config import sync_streamlit_secrets_to_env

st.title("Admin and Codebook")
sync_streamlit_secrets_to_env()
settings = get_settings()
codebook = load_codebook(settings.active_codebook_path)
model_registry = load_model_registry("config/models/model_registry.yaml")

tab_codebook, tab_models, tab_storage = st.tabs(["Codebook", "Models", "Prototype Storage"])


def renderable_codebook_rows() -> list[dict[str, Any]]:
    rows = []
    for variable in codebook.variables:
        row = variable.model_dump()
        for key, value in row.items():
            if isinstance(value, (list, dict)):
                row[key] = json.dumps(value, ensure_ascii=True)
        rows.append(row)
    return rows

with tab_codebook:
    st.write({"version": codebook.version, "variables": len(codebook.variables)})
    st.dataframe(renderable_codebook_rows(), use_container_width=True, hide_index=True)

with tab_models:
    st.caption("External LLM calls require explicit environment/secrets configuration.")
    st.json(
        {
            "allow_external_llm": settings.allow_external_llm,
            "openai_api_key_configured": bool(settings.openai_api_key),
            "openai_base_url": settings.openai_base_url,
            "openai_model": settings.openai_model,
            "gemini_api_key_configured": bool(settings.gemini_api_key),
            "gemini_base_url": settings.gemini_base_url,
            "gemini_model": settings.gemini_model,
        }
    )
    st.dataframe(
        [
            {"key": key, **resolve_runtime_model_config(config).model_dump()}
            for key, config in model_registry.models.items()
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_storage:
    if st.button("Initialize / check storage schema"):
        initialize_application_schema()
        st.success("Prototype storage schema is initialized.")
    status = get_schema_status()
    st.json(status)
