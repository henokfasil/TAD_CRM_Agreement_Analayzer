from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.services.codebook import load_codebook

st.title("Admin and Codebook")
codebook = load_codebook(get_settings().active_codebook_path)
st.write({"version": codebook.version, "variables": len(codebook.variables)})
st.dataframe([variable.model_dump() for variable in codebook.variables], use_container_width=True)
