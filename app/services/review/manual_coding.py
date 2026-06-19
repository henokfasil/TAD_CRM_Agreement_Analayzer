from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db


def initialize_review_tables(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_coding_decisions (
                decision_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                provision_id TEXT NOT NULL,
                variable_code TEXT NOT NULL,
                proposed_value TEXT NOT NULL,
                reviewer_status TEXT NOT NULL,
                evidence_quote TEXT NOT NULL,
                evidence_page INTEGER,
                reviewer_note TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
    return resolved_db_path


def build_manual_decision(
    document_id: str,
    provision: dict[str, Any],
    variable_code: str,
    proposed_value: str,
    reviewer_status: str,
    evidence_quote: str,
    reviewer_note: str,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    decision_id = f"{provision['provision_id']}:{variable_code}:{created_at}"
    return {
        "decision_id": decision_id,
        "document_id": document_id,
        "provision_id": provision["provision_id"],
        "variable_code": variable_code,
        "proposed_value": proposed_value,
        "reviewer_status": reviewer_status,
        "evidence_quote": evidence_quote,
        "evidence_page": provision["page_start"],
        "reviewer_note": reviewer_note,
        "created_at": created_at,
    }


def save_manual_decision(
    decision: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_review_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT INTO manual_coding_decisions (
                decision_id,
                document_id,
                provision_id,
                variable_code,
                proposed_value,
                reviewer_status,
                evidence_quote,
                evidence_page,
                reviewer_note,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision["decision_id"],
                decision["document_id"],
                decision["provision_id"],
                decision["variable_code"],
                decision["proposed_value"],
                decision["reviewer_status"],
                decision["evidence_quote"],
                decision["evidence_page"],
                decision["reviewer_note"],
                decision["created_at"],
            ),
        )


def load_manual_decisions(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> list[dict[str, Any]]:
    resolved_db_path = initialize_review_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM manual_coding_decisions
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def decisions_to_csv(decisions: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "decision_id",
            "document_id",
            "provision_id",
            "variable_code",
            "proposed_value",
            "reviewer_status",
            "evidence_page",
            "evidence_quote",
            "reviewer_note",
            "created_at",
        ],
    )
    writer.writeheader()
    for decision in decisions:
        writer.writerow({field: decision.get(field) for field in writer.fieldnames})
    return output.getvalue()

