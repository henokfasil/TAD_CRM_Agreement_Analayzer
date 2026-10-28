from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPORT_SPEC_PATH = Path("config/research/report_spec_v1.yaml")


def load_report_specification(path: Path | str = DEFAULT_REPORT_SPEC_PATH) -> dict[str, Any]:
    """Load and minimally validate the versioned research-report contract."""
    resolved = Path(path)
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Research report specification must be a mapping.")
    required = {"version", "objective", "analysis_registry", "publication_rules"}
    missing = required.difference(payload)
    if missing:
        raise ValueError(f"Research report specification is missing: {sorted(missing)}")
    if not isinstance(payload["analysis_registry"], list):
        raise ValueError("analysis_registry must be a list.")
    return payload
