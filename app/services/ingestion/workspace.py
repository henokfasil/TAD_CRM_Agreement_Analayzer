from __future__ import annotations

import csv
import io
import json
import tempfile
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.documents import ExtractionResult, StoredDocument

DEFAULT_WORKSPACE_DB_PATH = Path("data/processed/document_workspace.sqlite")


def fallback_workspace_db_path() -> Path:
    return Path(tempfile.gettempdir()) / "crm_agreement_intelligence" / "document_workspace.sqlite"


def build_document_record(
    stored: StoredDocument,
    extraction: ExtractionResult | None,
) -> dict[str, Any]:
    pages = []
    if extraction is not None:
        pages = [
            {
                "page_number": page.page_number,
                "text": page.text,
                "extraction_confidence": page.extraction_confidence,
            }
            for page in extraction.pages
        ]

    return {
        "document_id": stored.sha256_hash,
        "original_filename": stored.original_filename,
        "stored_path": str(stored.stored_path),
        "sha256_hash": stored.sha256_hash,
        "size_bytes": stored.size_bytes,
        "duplicate": stored.duplicate,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "extraction_method": extraction.method if extraction else None,
        "parser_version": extraction.parser_version if extraction else None,
        "page_count": len(pages),
        "pages": pages,
    }


def upsert_document_record(
    records: list[dict[str, Any]],
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    kept = [item for item in records if item["document_id"] != record["document_id"]]
    return [record, *kept]


def records_to_json(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, indent=2, ensure_ascii=False)


def pages_to_csv(records: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "document_id",
            "original_filename",
            "sha256_hash",
            "page_number",
            "text",
        ],
    )
    writer.writeheader()
    for record in records:
        for page in record.get("pages", []):
            writer.writerow(
                {
                    "document_id": record["document_id"],
                    "original_filename": record["original_filename"],
                    "sha256_hash": record["sha256_hash"],
                    "page_number": page["page_number"],
                    "text": page["text"],
                }
            )
    return output.getvalue()


def initialize_workspace_db(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    duplicate INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    extraction_method TEXT,
                    parser_version TEXT,
                    page_count INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_pages (
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    extraction_confidence REAL,
                    PRIMARY KEY (document_id, page_number),
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
                """
            )
    except sqlite3.OperationalError:
        if db_path != DEFAULT_WORKSPACE_DB_PATH:
            raise
        fallback_path = fallback_workspace_db_path()
        return initialize_workspace_db(fallback_path)
    return db_path


def save_document_record(
    record: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO documents (
                document_id,
                original_filename,
                stored_path,
                sha256_hash,
                size_bytes,
                duplicate,
                created_at,
                extraction_method,
                parser_version,
                page_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["document_id"],
                record["original_filename"],
                record["stored_path"],
                record["sha256_hash"],
                record["size_bytes"],
                int(record["duplicate"]),
                record["created_at"],
                record["extraction_method"],
                record["parser_version"],
                record["page_count"],
            ),
        )
        connection.execute(
            "DELETE FROM document_pages WHERE document_id = ?",
            (record["document_id"],),
        )
        connection.executemany(
            """
            INSERT INTO document_pages (
                document_id,
                page_number,
                text,
                extraction_confidence
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    record["document_id"],
                    page["page_number"],
                    page["text"],
                    page["extraction_confidence"],
                )
                for page in record.get("pages", [])
            ],
        )


def load_document_records(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        document_rows = connection.execute(
            """
            SELECT *
            FROM documents
            ORDER BY created_at DESC
            """
        ).fetchall()
        page_rows = connection.execute(
            """
            SELECT *
            FROM document_pages
            ORDER BY document_id, page_number
            """
        ).fetchall()

    pages_by_document: dict[str, list[dict[str, Any]]] = {}
    for row in page_rows:
        pages_by_document.setdefault(row["document_id"], []).append(
            {
                "page_number": row["page_number"],
                "text": row["text"],
                "extraction_confidence": row["extraction_confidence"],
            }
        )

    return [
        {
            "document_id": row["document_id"],
            "original_filename": row["original_filename"],
            "stored_path": row["stored_path"],
            "sha256_hash": row["sha256_hash"],
            "size_bytes": row["size_bytes"],
            "duplicate": bool(row["duplicate"]),
            "created_at": row["created_at"],
            "extraction_method": row["extraction_method"],
            "parser_version": row["parser_version"],
            "page_count": row["page_count"],
            "pages": pages_by_document.get(row["document_id"], []),
        }
        for row in document_rows
    ]


def count_document_records(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> int:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0])


def clear_document_records(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> None:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute("DELETE FROM document_pages")
        connection.execute("DELETE FROM documents")
