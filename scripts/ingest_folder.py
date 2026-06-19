from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.ingestion.storage import store_upload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    settings = get_settings()
    for path in args.folder.iterdir():
        if path.is_file():
            stored = store_upload(path, settings.upload_dir)
            print(f"{path.name}: {stored.sha256_hash} duplicate={stored.duplicate}")


if __name__ == "__main__":
    main()
