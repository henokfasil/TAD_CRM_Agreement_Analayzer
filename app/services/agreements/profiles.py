from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db
from app.services.storage.persistent import get_record, load_records, upsert_record, uses_persistent_store


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
                legal_status TEXT,
                bindingness_status TEXT,
                entry_into_force_date TEXT,
                countries_json TEXT,
                organisations_json TEXT,
                g7_participation TEXT,
                global_south_participation TEXT,
                producer_consumer_pair TEXT,
                validation_status TEXT,
                metadata_sources TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(agreement_profiles)").fetchall()
        }
        new_columns = {
            "legal_status": "TEXT",
            "bindingness_status": "TEXT",
            "entry_into_force_date": "TEXT",
            "countries_json": "TEXT",
            "organisations_json": "TEXT",
            "g7_participation": "TEXT",
            "global_south_participation": "TEXT",
            "producer_consumer_pair": "TEXT",
            "validation_status": "TEXT",
            "metadata_sources": "TEXT",
        }
        for column, data_type in new_columns.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE agreement_profiles ADD COLUMN {column} {data_type}"
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
    legal_status: str = "",
    bindingness_status: str = "unknown",
    entry_into_force_date: str = "",
    countries: list[str] | None = None,
    organisations: list[str] | None = None,
    g7_participation: str = "unknown",
    global_south_participation: str = "unknown",
    producer_consumer_pair: str = "unknown",
    validation_status: str = "provisional",
    metadata_sources: str = "",
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
        "legal_status": legal_status.strip(),
        "bindingness_status": bindingness_status.strip() or "unknown",
        "entry_into_force_date": entry_into_force_date.strip(),
        "countries": [value.strip() for value in (countries or []) if value.strip()],
        "organisations": [value.strip() for value in (organisations or []) if value.strip()],
        "g7_participation": g7_participation.strip() or "unknown",
        "global_south_participation": global_south_participation.strip() or "unknown",
        "producer_consumer_pair": producer_consumer_pair.strip() or "unknown",
        "validation_status": validation_status.strip() or "provisional",
        "metadata_sources": metadata_sources.strip(),
        "notes": notes.strip(),
        "created_at": now,
        "updated_at": now,
    }


def save_agreement_profile(
    profile: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    if uses_persistent_store(db_path):
        existing = get_record("agreement_profiles", profile["agreement_id"])
        saved = {
            **profile,
            "created_at": existing["created_at"] if existing else profile["created_at"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        upsert_record("agreement_profiles", profile["agreement_id"], saved)
        return
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
                legal_status,
                bindingness_status,
                entry_into_force_date,
                countries_json,
                organisations_json,
                g7_participation,
                global_south_participation,
                producer_consumer_pair,
                validation_status,
                metadata_sources,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                profile.get("legal_status", ""),
                profile.get("bindingness_status", "unknown"),
                profile.get("entry_into_force_date", ""),
                json.dumps(profile.get("countries", []), ensure_ascii=False),
                json.dumps(profile.get("organisations", []), ensure_ascii=False),
                profile.get("g7_participation", "unknown"),
                profile.get("global_south_participation", "unknown"),
                profile.get("producer_consumer_pair", "unknown"),
                profile.get("validation_status", "provisional"),
                profile.get("metadata_sources", ""),
                profile["notes"],
                created_at,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def load_agreement_profiles(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> list[dict[str, Any]]:
    if uses_persistent_store(db_path):
        return load_records("agreement_profiles")
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
    return [_deserialise_profile(dict(row)) for row in rows]


def get_agreement_profile(
    agreement_id: str,
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> dict[str, Any] | None:
    if uses_persistent_store(db_path):
        return get_record("agreement_profiles", agreement_id)
    resolved_db_path = initialize_agreement_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM agreement_profiles WHERE agreement_id = ?",
            (agreement_id,),
        ).fetchone()
    return _deserialise_profile(dict(row)) if row else None


def _deserialise_profile(profile: dict[str, Any]) -> dict[str, Any]:
    for stored, public in (
        ("countries_json", "countries"),
        ("organisations_json", "organisations"),
    ):
        raw = profile.pop(stored, None)
        try:
            profile[public] = json.loads(raw) if raw else []
        except (TypeError, json.JSONDecodeError):
            profile[public] = []
    profile["bindingness_status"] = profile.get("bindingness_status") or "unknown"
    profile["g7_participation"] = profile.get("g7_participation") or "unknown"
    profile["global_south_participation"] = (
        profile.get("global_south_participation") or "unknown"
    )
    profile["producer_consumer_pair"] = profile.get("producer_consumer_pair") or "unknown"
    profile["validation_status"] = profile.get("validation_status") or "provisional"
    return profile


def link_document_to_agreement(
    agreement_id: str,
    document_id: str,
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    if uses_persistent_store(db_path):
        link = {
            "agreement_id": agreement_id,
            "document_id": document_id,
            "linked_at": datetime.now(timezone.utc).isoformat(),
        }
        upsert_record("agreement_documents", f"{agreement_id}:{document_id}", link)
        return
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
    if uses_persistent_store(db_path):
        return load_records("agreement_documents")
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
        "legal_status",
        "bindingness_status",
        "entry_into_force_date",
        "countries",
        "organisations",
        "g7_participation",
        "global_south_participation",
        "producer_consumer_pair",
        "validation_status",
        "metadata_sources",
        "notes",
        "created_at",
        "updated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for profile in profiles:
        writer.writerow({field: profile.get(field) for field in fieldnames})
    return output.getvalue()
