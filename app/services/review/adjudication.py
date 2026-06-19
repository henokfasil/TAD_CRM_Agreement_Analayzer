from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db


def initialize_adjudication_tables(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS adjudication_decisions (
                adjudication_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                provision_id TEXT NOT NULL,
                variable_code TEXT NOT NULL,
                final_value TEXT NOT NULL,
                rationale TEXT NOT NULL,
                adjudicator_id TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    return resolved_db_path


def build_adjudication_decision(
    source_type: str,
    source: dict[str, Any],
    final_value: str,
    rationale: str,
    adjudicator_id: str,
) -> dict[str, Any]:
    source_id_key = "decision_id" if source_type == "manual" else "proposal_id"
    return {
        "adjudication_id": str(uuid4()),
        "source_type": source_type,
        "source_id": source[source_id_key],
        "document_id": source["document_id"],
        "provision_id": source["provision_id"],
        "variable_code": source["variable_code"],
        "final_value": final_value,
        "rationale": rationale,
        "adjudicator_id": adjudicator_id,
        "validation_status": "adjudicated",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_adjudication_decision(
    decision: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_adjudication_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT INTO adjudication_decisions (
                adjudication_id,
                source_type,
                source_id,
                document_id,
                provision_id,
                variable_code,
                final_value,
                rationale,
                adjudicator_id,
                validation_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision["adjudication_id"],
                decision["source_type"],
                decision["source_id"],
                decision["document_id"],
                decision["provision_id"],
                decision["variable_code"],
                decision["final_value"],
                decision["rationale"],
                decision["adjudicator_id"],
                decision["validation_status"],
                decision["created_at"],
            ),
        )


def load_adjudication_decisions(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    resolved_db_path = initialize_adjudication_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM adjudication_decisions
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def adjudications_to_csv(decisions: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "adjudication_id",
        "source_type",
        "source_id",
        "document_id",
        "provision_id",
        "variable_code",
        "final_value",
        "rationale",
        "adjudicator_id",
        "validation_status",
        "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for decision in decisions:
        writer.writerow({field: decision.get(field) for field in fieldnames})
    return output.getvalue()

