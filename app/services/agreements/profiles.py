from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db


def initialize_agreement_tables(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agreement_profiles (
                agreement_id TEXT PRIMARY KEY,
                canonical_title TEXT NOT NULL,
                short_title TEXT,
                agreement_type TEXT,
                parties TEXT,
                signature_date TEXT,
                source_language TEXT,
                inclusion_status TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agreement_documents (
                agreement_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                PRIMARY KEY (agreement_id, document_id),
                FOREIGN KEY (agreement_id) REFERENCES agreement_profiles(agreement_id)
            )
            """
        )
    return resolved_db_path


def build_agreement_profile(
    canonical_title: str,
    short_title: str = "",
    agreement_type: str = "",
    parties: str = "",
    signature_date: str = "",
    source_language: str = "",
    inclusion_status: str = "pending",
    notes: str = "",
    agreement_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "agreement_id": agreement_id or str(uuid4()),
        "canonical_title": canonical_title.strip(),
        "short_title": short_title.strip(),
        "agreement_type": agreement_type.strip(),
        "parties": parties.strip(),
        "signature_date": signature_date.strip(),
        "source_language": source_language.strip(),
        "inclusion_status": inclusion_status.strip() or "pending",
        "notes": notes.strip(),
        "created_at": now,
        "updated_at": now,
    }


def save_agreement_profile(
    profile: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_agreement_tables(db_path)
    existing = get_agreement_profile(profile["agreement_id"], db_path)
    created_at = existing["created_at"] if existing else profile["created_at"]
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO agreement_profiles (
                agreement_id,
                canonical_title,
                short_title,
                agreement_type,
                parties,
                signature_date,
                source_language,
                inclusion_status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile["agreement_id"],
                profile["canonical_title"],
                profile["short_title"],
                profile["agreement_type"],
                profile["parties"],
                profile["signature_date"],
                profile["source_language"],
                profile["inclusion_status"],
                profile["notes"],
                created_at,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_agreement_profiles(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> list[dict[str, Any]]:
    resolved_db_path = initialize_agreement_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM agreement_profiles
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_agreement_profile(
    agreement_id: str,
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> dict[str, Any] | None:
    resolved_db_path = initialize_agreement_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM agreement_profiles WHERE agreement_id = ?",
            (agreement_id,),
        ).fetchone()
    return dict(row) if row else None


def link_document_to_agreement(
    agreement_id: str,
    document_id: str,
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_agreement_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO agreement_documents (
                agreement_id,
                document_id,
                linked_at
            )
            VALUES (?, ?, ?)
            """,
            (agreement_id, document_id, datetime.now(timezone.utc).isoformat()),
        )


def load_agreement_document_links(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    resolved_db_path = initialize_agreement_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM agreement_documents
            ORDER BY linked_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def agreement_profiles_to_csv(profiles: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "agreement_id",
        "canonical_title",
        "short_title",
        "agreement_type",
        "parties",
        "signature_date",
        "source_language",
        "inclusion_status",
        "notes",
        "created_at",
        "updated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for profile in profiles:
        writer.writerow({field: profile.get(field) for field in fieldnames})
    return output.getvalue()

