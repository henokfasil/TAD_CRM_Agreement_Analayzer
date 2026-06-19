from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.services.codebook import load_codebook
from app.services.storage.schema import get_schema_status, initialize_application_schema

st.title("Admin and Codebook")
settings = get_settings()
codebook = load_codebook(settings.active_codebook_path)

tab_codebook, tab_storage = st.tabs(["Codebook", "Prototype Storage"])

with tab_codebook:
    st.write({"version": codebook.version, "variables": len(codebook.variables)})
    st.dataframe([variable.model_dump() for variable in codebook.variables], use_container_width=True)

with tab_storage:
    if st.button("Initialize / check storage schema"):
        initialize_application_schema()
        st.success("Prototype storage schema is initialized.")
    status = get_schema_status()
    st.json(status)
