from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.agreements.profiles import initialize_agreement_tables
from app.services.classification.ai_coding import initialize_ai_coding_tables
from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db
from app.services.review.manual_coding import initialize_review_tables
from app.services.verification.ai_verification import initialize_verification_tables

CURRENT_SCHEMA_VERSION = 1


def initialize_application_schema(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    initialize_agreement_tables(resolved_db_path)
    initialize_review_tables(resolved_db_path)
    initialize_ai_coding_tables(resolved_db_path)
    initialize_verification_tables(resolved_db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO schema_migrations (
                version,
                description,
                applied_at
            )
            VALUES (?, ?, ?)
            """,
            (
                CURRENT_SCHEMA_VERSION,
                "prototype workspace schema",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return resolved_db_path


def get_schema_status(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> dict[str, Any]:
    resolved_db_path = initialize_application_schema(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        versions = connection.execute(
            """
            SELECT *
            FROM schema_migrations
            ORDER BY version
            """
        ).fetchall()
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
    return {
        "db_path": str(resolved_db_path),
        "current_schema_version": CURRENT_SCHEMA_VERSION,
        "applied_versions": [dict(row) for row in versions],
        "tables": [row["name"] for row in tables],
    }
