from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.services.codebook import load_codebook
from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db
from app.services.storage.persistent import (
    get_record,
    load_records,
    upsert_record,
    uses_persistent_store,
)


DEFAULT_QUESTION_MAP_PATH = Path("config/research/question_map_v1.yaml")
ANSWER_OPTIONS = ["Yes", "No", "Mixed", "Unclear", "Not reviewed"]


def load_question_map(path: str | Path = DEFAULT_QUESTION_MAP_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("questions"), list):
        raise ValueError("Research question map must define a questions list.")
    return payload


def initialize_answer_sheet_tables(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> Path:
    resolved = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS research_question_reviews (
                review_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                final_answer TEXT NOT NULL,
                final_summary TEXT NOT NULL,
                rationale TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agreement_research_approvals (
                document_id TEXT PRIMARY KEY,
                reviewer_id TEXT NOT NULL,
                rationale TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                approved_at TEXT NOT NULL
            )
            """
        )
    return resolved


def build_question_review(
    document_id: str,
    question_id: str,
    final_answer: str,
    final_summary: str,
    rationale: str,
    reviewer_id: str,
) -> dict[str, Any]:
    return {
        "review_id": f"{document_id}:{question_id}",
        "document_id": document_id,
        "question_id": question_id,
        "final_answer": final_answer,
        "final_summary": final_summary.strip(),
        "rationale": rationale.strip(),
        "reviewer_id": reviewer_id.strip(),
        "validation_status": "validated",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_question_review(
    review: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    if uses_persistent_store(db_path):
        upsert_record("research_question_reviews", review["review_id"], review)
        approval = get_record("agreement_research_approvals", review["document_id"])
        if approval:
            upsert_record(
                "agreement_research_approvals",
                review["document_id"],
                {**approval, "validation_status": "needs_reapproval"},
            )
        return
    resolved = initialize_answer_sheet_tables(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO research_question_reviews (
                review_id, document_id, question_id, final_answer, final_summary,
                rationale, reviewer_id, validation_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(
                review[key]
                for key in (
                    "review_id",
                    "document_id",
                    "question_id",
                    "final_answer",
                    "final_summary",
                    "rationale",
                    "reviewer_id",
                    "validation_status",
                    "updated_at",
                )
            ),
        )
        connection.execute(
            """
            UPDATE agreement_research_approvals
            SET validation_status = 'needs_reapproval'
            WHERE document_id = ?
            """,
            (review["document_id"],),
        )


def load_question_reviews(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    if uses_persistent_store(db_path):
        return load_records("research_question_reviews")
    resolved = initialize_answer_sheet_tables(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM research_question_reviews ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def build_agreement_approval(
    document_id: str,
    reviewer_id: str,
    rationale: str,
) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "reviewer_id": reviewer_id.strip(),
        "rationale": rationale.strip(),
        "validation_status": "approved",
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }


def save_agreement_approval(
    approval: dict[str, Any],
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> None:
    if uses_persistent_store(db_path):
        upsert_record("agreement_research_approvals", approval["document_id"], approval)
        return
    resolved = initialize_answer_sheet_tables(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO agreement_research_approvals (
                document_id, reviewer_id, rationale, validation_status, approved_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            tuple(
                approval[key]
                for key in (
                    "document_id",
                    "reviewer_id",
                    "rationale",
                    "validation_status",
                    "approved_at",
                )
            ),
        )


def load_agreement_approvals(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    if uses_persistent_store(db_path):
        return load_records("agreement_research_approvals")
    resolved = initialize_answer_sheet_tables(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM agreement_research_approvals ORDER BY approved_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def _positive(value: Any) -> bool:
    normalised = str(value).strip().lower()
    return normalised not in {"", "0", "no", "false", "none", "unknown", "not applicable"}


def _profile_for_document(
    document_id: str,
    profiles: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> dict[str, Any] | None:
    agreement_ids = {
        link.get("agreement_id") for link in links if link.get("document_id") == document_id
    }
    return next(
        (profile for profile in profiles if profile.get("agreement_id") in agreement_ids),
        None,
    )


def _latest_by_variable(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for record in sorted(records, key=lambda row: row.get("created_at", ""), reverse=True):
        selected.setdefault(str(record.get("variable_code")), record)
    return selected


def build_answer_sheet(
    document_id: str,
    profiles: list[dict[str, Any]],
    links: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    manual_decisions: list[dict[str, Any]],
    ai_proposals: list[dict[str, Any]],
    reviews: list[dict[str, Any]],
    question_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    mapping = question_map or load_question_map()
    codebook = load_codebook("config/codebooks/crm_codebook_v1.yaml")
    labels = {variable.code: variable.label for variable in codebook.variables}
    profile = _profile_for_document(document_id, profiles, links)
    final_records = _latest_by_variable(
        [row for row in adjudications if row.get("document_id") == document_id]
    )
    manual_records = _latest_by_variable(
        [row for row in manual_decisions if row.get("document_id") == document_id]
    )
    ai_records = _latest_by_variable(
        [row for row in ai_proposals if row.get("document_id") == document_id]
    )
    source_records = {
        str(row.get("decision_id") or row.get("proposal_id")): row
        for row in [*manual_decisions, *ai_proposals]
    }
    saved_reviews = {
        row["question_id"]: row
        for row in reviews
        if row.get("document_id") == document_id
    }
    answers = []
    for question in mapping["questions"]:
        question_id = question["id"]
        evidence = []
        used = []
        for code in question.get("variable_codes", []):
            record = final_records.get(code) or manual_records.get(code) or ai_records.get(code)
            if not record:
                continue
            value = record.get("final_value", record.get("proposed_value"))
            source = source_records.get(str(record.get("source_id")), record)
            used.append({"code": code, "label": labels.get(code, code), "value": value})
            quote = source.get("evidence_quote")
            if quote:
                evidence.append(
                    {
                        "page": source.get("evidence_page"),
                        "quote": quote,
                        "variable": labels.get(code, code),
                    }
                )

        proposed_answer = "Not reviewed"
        summary = "No coded evidence is available for this question yet."
        if question_id == "participants":
            countries = list((profile or {}).get("countries") or [])
            organisations = list((profile or {}).get("organisations") or [])
            if countries or organisations:
                proposed_answer = "Yes"
                parts = []
                if countries:
                    parts.append(f"Countries: {', '.join(countries)}")
                if organisations:
                    parts.append(f"Organisations: {', '.join(organisations)}")
                summary = ". ".join(parts) + "."
            else:
                summary = "Participant metadata has not yet been completed for this agreement."
        elif question_id == "legal_bindingness" and profile and profile.get("bindingness_status") not in {
            None,
            "",
            "unknown",
        }:
            proposed_answer = "Yes" if profile["bindingness_status"] == "binding" else "Mixed"
            summary = (
                f"The agreement profile classifies this instrument as "
                f"{profile['bindingness_status']}."
            )
        elif used:
            positives = [item for item in used if _positive(item["value"])]
            proposed_answer = "Yes" if positives else "No"
            if positives:
                summary = "Evidence supports: " + "; ".join(
                    item["label"] for item in positives
                ) + "."
            else:
                summary = "Reviewed variables currently contain no positive finding."

        review = saved_reviews.get(question_id)
        answers.append(
            {
                "question_id": question_id,
                "question": question["question"],
                "answer": review.get("final_answer") if review else proposed_answer,
                "summary": review.get("final_summary") if review else summary,
                "rationale": review.get("rationale", "") if review else "",
                "validation_status": review.get("validation_status", "provisional")
                if review
                else "provisional",
                "evidence": evidence,
                "variables": used,
            }
        )
    return answers
