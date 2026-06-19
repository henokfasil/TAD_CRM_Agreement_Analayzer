from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db


def initialize_verification_tables(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_verification_results (
                verification_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                support_status TEXT NOT NULL,
                contradiction_status TEXT NOT NULL,
                verified_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                critique TEXT NOT NULL,
                missing_evidence INTEGER NOT NULL,
                human_review_required INTEGER NOT NULL,
                verifier_model TEXT NOT NULL,
                verifier_prompt_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    return resolved_db_path


def run_mock_verification(proposal: dict[str, Any]) -> dict[str, Any]:
    missing_evidence = not bool(str(proposal.get("evidence_quote", "")).strip())
    rule_conflict = proposal.get("rule_status") == "violation"
    supports = not missing_evidence and not rule_conflict
    critique_parts = []
    if missing_evidence:
        critique_parts.append("No evidence quote was provided.")
    if rule_conflict:
        critique_parts.append("The proposal has an unresolved codebook dependency conflict.")
    if not critique_parts:
        critique_parts.append("The proposal has evidence and no detected dependency conflict.")
    created_at = datetime.now(timezone.utc).isoformat()
    return {
        "verification_id": f"{proposal['proposal_id']}:verification:{created_at}",
        "proposal_id": proposal["proposal_id"],
        "support_status": "supports" if supports else "does_not_support",
        "contradiction_status": "none_detected" if supports else "needs_review",
        "verified_value": str(proposal.get("proposed_value", "")),
        "confidence": 0.75 if supports else 0.4,
        "critique": " ".join(critique_parts),
        "missing_evidence": missing_evidence,
        "human_review_required": True,
        "verifier_model": "mock-verifier-v1",
        "verifier_prompt_version": "verification_mock_v1",
        "created_at": created_at,
    }


def save_verification_result(
    result: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_verification_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT INTO ai_verification_results (
                verification_id,
                proposal_id,
                support_status,
                contradiction_status,
                verified_value,
                confidence,
                critique,
                missing_evidence,
                human_review_required,
                verifier_model,
                verifier_prompt_version,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["verification_id"],
                result["proposal_id"],
                result["support_status"],
                result["contradiction_status"],
                result["verified_value"],
                result["confidence"],
                result["critique"],
                int(result["missing_evidence"]),
                int(result["human_review_required"]),
                result["verifier_model"],
                result["verifier_prompt_version"],
                result["created_at"],
            ),
        )


def load_verification_results(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> list[dict[str, Any]]:
    resolved_db_path = initialize_verification_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM ai_verification_results
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [
        {
            **dict(row),
            "missing_evidence": bool(row["missing_evidence"]),
            "human_review_required": bool(row["human_review_required"]),
        }
        for row in rows
    ]


def verification_results_to_csv(results: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "verification_id",
        "proposal_id",
        "support_status",
        "contradiction_status",
        "verified_value",
        "confidence",
        "critique",
        "missing_evidence",
        "human_review_required",
        "verifier_model",
        "verifier_prompt_version",
        "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for result in results:
        writer.writerow({field: result.get(field) for field in fieldnames})
    return output.getvalue()

