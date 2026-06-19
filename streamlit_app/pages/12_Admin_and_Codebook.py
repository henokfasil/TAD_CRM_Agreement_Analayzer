from __future__ import annotations

import streamlit as st

from app.core.config import get_settings
from app.services.codebook import load_codebook

st.title("Admin and Codebook")
codebook = load_codebook(get_settings().active_codebook_path)
st.write({"version": codebook.version, "variables": len(codebook.variables)})
st.dataframe([variable.model_dump() for variable in codebook.variables], use_container_width=True)

