from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from app.core.security import safe_filename
from app.schemas.documents import StoredDocument


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def store_upload(source_path: Path, upload_dir: Path, original_filename: str | None = None) -> StoredDocument:
    upload_dir.mkdir(parents=True, exist_ok=True)
    digest = sha256_file(source_path)
    filename = safe_filename(original_filename or source_path.name)
    suffix = Path(filename).suffix
    stored_path = upload_dir / f"{digest}{suffix}"
    duplicate = stored_path.exists()
    if not duplicate:
        shutil.copy2(source_path, stored_path)
    return StoredDocument(
        original_filename=filename,
        stored_path=stored_path,
        sha256_hash=digest,
        size_bytes=source_path.stat().st_size,
        duplicate=duplicate,
    )

