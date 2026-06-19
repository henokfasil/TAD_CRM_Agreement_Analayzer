from app.services.codebook import load_codebook


def test_active_codebook_loads() -> None:
    codebook = load_codebook("config/codebooks/active_codebook.yaml")
    codes = {variable.code for variable in codebook.variables}
    assert codebook.version == "v1"
    assert "inv_spec_def" in codes
    assert "enforceability_levels" in codes
    assert len(codebook.variables) >= 80

