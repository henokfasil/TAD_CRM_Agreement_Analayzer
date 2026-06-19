from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.llm.registry import build_provider, get_model_config, load_model_registry
from app.schemas.codebook import CodebookVariableSchema
from app.schemas.llm import LLMMessage, LLMRequest
from app.services.classification.rules import evaluate_dependency_rules
from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db


def initialize_ai_coding_tables(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved_db_path = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_coding_proposals (
                proposal_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                provision_id TEXT NOT NULL,
                variable_code TEXT NOT NULL,
                proposed_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_quote TEXT NOT NULL,
                evidence_page INTEGER,
                reasoning_summary TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_provider TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                codebook_version TEXT NOT NULL,
                rule_status TEXT NOT NULL,
                reviewer_status TEXT NOT NULL,
                verification_status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    return resolved_db_path


def build_ai_coding_request(
    provision: dict[str, Any],
    variable: CodebookVariableSchema,
    model_name: str,
) -> LLMRequest:
    return LLMRequest(
        model=model_name,
        temperature=0,
        response_format="json",
        metadata={
            "prompt_version": "coding_mock_v1",
            "variable_code": variable.code,
            "segmentation_version": provision.get("segmentation_version"),
        },
        messages=[
            LLMMessage(
                role="system",
                content=(
                    "You propose provisional CRM agreement coding as JSON. "
                    "All outputs require human review."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Variable: {variable.code}\n"
                    f"Definition: {variable.description}\n"
                    f"Allowed values: {variable.allowed_values}\n"
                    f"Provision text: {provision['provision_text']}"
                ),
            ),
        ],
    )


def run_ai_coding_proposal(
    document_id: str,
    provision: dict[str, Any],
    variable: CodebookVariableSchema,
    existing_decisions: list[dict[str, Any]],
    codebook_version: str,
    model_registry_path: str | Path = "config/models/model_registry.yaml",
    model_key: str = "coding_model_v1",
) -> dict[str, Any]:
    registry = load_model_registry(model_registry_path)
    model_config = get_model_config(registry, model_key)
    provider = build_provider(model_config)
    request = build_ai_coding_request(provision, variable, model_config.model_name)
    response = provider.complete(request)
    structured = response.structured_output or {}
    proposed_value = str(structured.get("proposed_value", "0"))
    rule_result = evaluate_dependency_rules(
        variable,
        proposed_value,
        existing_decisions,
        provision["provision_id"],
    )
    created_at = datetime.now(timezone.utc).isoformat()
    return {
        "proposal_id": f"{provision['provision_id']}:{variable.code}:{created_at}",
        "document_id": document_id,
        "provision_id": provision["provision_id"],
        "variable_code": variable.code,
        "proposed_value": proposed_value,
        "confidence": float(structured.get("confidence", 0)),
        "evidence_quote": str(structured.get("evidence_quote", "")),
        "evidence_page": provision.get("page_start"),
        "reasoning_summary": str(structured.get("reasoning_summary", "")),
        "model_name": response.model,
        "model_provider": response.provider,
        "prompt_version": request.metadata["prompt_version"],
        "codebook_version": codebook_version,
        "rule_status": rule_result["status"],
        "reviewer_status": "pending",
        "verification_status": "not_verified",
        "created_at": created_at,
    }


def save_ai_coding_proposal(
    proposal: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    resolved_db_path = initialize_ai_coding_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.execute(
            """
            INSERT INTO ai_coding_proposals (
                proposal_id,
                document_id,
                provision_id,
                variable_code,
                proposed_value,
                confidence,
                evidence_quote,
                evidence_page,
                reasoning_summary,
                model_name,
                model_provider,
                prompt_version,
                codebook_version,
                rule_status,
                reviewer_status,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal["proposal_id"],
                proposal["document_id"],
                proposal["provision_id"],
                proposal["variable_code"],
                proposal["proposed_value"],
                proposal["confidence"],
                proposal["evidence_quote"],
                proposal["evidence_page"],
                proposal["reasoning_summary"],
                proposal["model_name"],
                proposal["model_provider"],
                proposal["prompt_version"],
                proposal["codebook_version"],
                proposal["rule_status"],
                proposal["reviewer_status"],
                proposal["verification_status"],
                proposal["created_at"],
            ),
        )


def load_ai_coding_proposals(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> list[dict[str, Any]]:
    resolved_db_path = initialize_ai_coding_tables(db_path)
    with sqlite3.connect(resolved_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM ai_coding_proposals
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def ai_proposals_to_csv(proposals: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fieldnames = [
        "proposal_id",
        "document_id",
        "provision_id",
        "variable_code",
        "proposed_value",
        "confidence",
        "evidence_page",
        "evidence_quote",
        "reasoning_summary",
        "model_name",
        "model_provider",
        "prompt_version",
        "codebook_version",
        "rule_status",
        "reviewer_status",
        "verification_status",
        "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for proposal in proposals:
        writer.writerow({field: proposal.get(field) for field in fieldnames})
    return output.getvalue()

