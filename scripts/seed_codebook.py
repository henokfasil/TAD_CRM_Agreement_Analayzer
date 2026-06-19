from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.codebook import load_codebook


def main() -> None:
    codebook = load_codebook(get_settings().active_codebook_path)
    print(f"Loaded {len(codebook.variables)} variables from {codebook.version}.")


if __name__ == "__main__":
    main()
