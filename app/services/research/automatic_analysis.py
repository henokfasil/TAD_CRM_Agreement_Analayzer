from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.llm.registry import (
    build_provider,
    get_model_config,
    load_model_registry,
    resolve_runtime_model_config,
)
from app.schemas.llm import LLMMessage, LLMRequest
from app.services.ingestion.workspace import DEFAULT_WORKSPACE_DB_PATH, initialize_workspace_db
from app.services.research.answer_sheet import load_question_map
from app.services.storage.persistent import load_records, upsert_record, uses_persistent_store


COLLECTION = "agreement_automatic_analyses"
PROMPT_VERSION = "agreement_research_analysis_v1"
ALLOWED_ANSWERS = {"Yes", "No", "Mixed", "Unclear"}


def available_analysis_models(
    registry_path: str | Path = "config/models/model_registry.yaml",
) -> dict[str, Any]:
    registry = load_model_registry(registry_path)
    return {
        key: resolve_runtime_model_config(config)
        for key, config in registry.models.items()
        if config.provider in {"openai_compatible", "gemini"}
    }


def _document_text(document: dict[str, Any], maximum_characters: int = 120_000) -> str:
    sections: list[str] = []
    used = 0
    for page in document.get("pages", []):
        text = str(page.get("text", "")).strip()
        if not text:
            continue
        section = f"\n--- PAGE {page.get('page_number')} ---\n{text[:12_000]}"
        if used + len(section) > maximum_characters:
            remaining = maximum_characters - used
            if remaining > 100:
                sections.append(section[:remaining])
            break
        sections.append(section)
        used += len(section)
    return "".join(sections)


def build_analysis_request(
    document: dict[str, Any],
    model_name: str,
    question_map: dict[str, Any] | None = None,
) -> LLMRequest:
    mapping = question_map or load_question_map()
    questions = [
        {"question_id": item["id"], "question": item["question"]}
        for item in mapping["questions"]
    ]
    source_text = _document_text(document)
    if not source_text:
        raise ValueError("The agreement has no readable extracted text.")
    return LLMRequest(
        model=model_name,
        temperature=0,
        response_format="json",
        metadata={"prompt_version": PROMPT_VERSION},
        messages=[
            LLMMessage(
                role="system",
                content=(
                    "You are analysing a critical-raw-materials agreement for comparative policy "
                    "research. Return one valid JSON object only. Do not infer a positive finding "
                    "without textual evidence. Every quotation must be copied exactly from the "
                    "provided page. Use Yes, No, Mixed, or Unclear. A No answer means the supplied "
                    "document was searched and the topic was not found; explain this without "
                    "inventing a quotation. Keep summaries concise and factual."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"Document: {document.get('original_filename')}\n\n"
                    "Extract agreement metadata and answer all research questions. Return this shape:\n"
                    "{\n"
                    '  "profile": {"title": "", "countries": [], "organisations": [], '
                    '"agreement_date": "", "bindingness": "binding|non-binding|mixed|unclear"},\n'
                    '  "answers": [{"question_id": "", "answer": "Yes|No|Mixed|Unclear", '
                    '"summary": "", "confidence": 0.0, "reasoning": "", '
                    '"evidence": [{"page": 1, "quote": "exact quotation"}]}]\n'
                    "}\n\n"
                    f"Questions:\n{json.dumps(questions, ensure_ascii=False)}\n\n"
                    f"Agreement text:{source_text}"
                ),
            ),
        ],
    )


def _json_payload(content: str, structured: dict[str, Any] | None) -> dict[str, Any]:
    if structured:
        return structured
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("The analysis model did not return a JSON object.")
    return payload


def _locate_quote(quote: str, pages: list[dict[str, Any]]) -> tuple[int | None, str] | None:
    quote = " ".join(str(quote).split()).strip()
    if not quote:
        return None
    quote_lower = quote.casefold()
    for page in pages:
        page_text = " ".join(str(page.get("text", "")).split())
        position = page_text.casefold().find(quote_lower)
        if position >= 0:
            return int(page.get("page_number")), page_text[position : position + len(quote)]
    return None


def _normalise_result(
    document: dict[str, Any], payload: dict[str, Any], question_map: dict[str, Any]
) -> dict[str, Any]:
    raw_answers = {
        str(item.get("question_id")): item
        for item in payload.get("answers", [])
        if isinstance(item, dict)
    }
    answers = []
    for question in question_map["questions"]:
        raw = raw_answers.get(question["id"], {})
        answer = str(raw.get("answer", "Unclear")).title()
        if answer not in ALLOWED_ANSWERS:
            answer = "Unclear"
        evidence = []
        rejected_quotes = 0
        for item in raw.get("evidence", []) or []:
            if not isinstance(item, dict):
                continue
            located = _locate_quote(str(item.get("quote", "")), document.get("pages", []))
            if located:
                page, quote = located
                evidence.append({"page": page, "quote": quote})
            else:
                rejected_quotes += 1
        confidence = max(0.0, min(1.0, float(raw.get("confidence", 0))))
        if answer in {"Yes", "Mixed"} and not evidence:
            answer = "Unclear"
            confidence = min(confidence, 0.35)
        answers.append(
            {
                "question_id": question["id"],
                "question": question["question"],
                "answer": answer,
                "summary": str(raw.get("summary") or "The automatic analysis was inconclusive."),
                "confidence": confidence,
                "reasoning": str(raw.get("reasoning") or ""),
                "evidence": evidence,
                "rejected_quotes": rejected_quotes,
            }
        )
    profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}
    return {
        "profile": {
            "title": str(profile.get("title") or document.get("original_filename", "")),
            "countries": [str(value) for value in profile.get("countries", []) or []],
            "organisations": [str(value) for value in profile.get("organisations", []) or []],
            "agreement_date": str(profile.get("agreement_date") or ""),
            "bindingness": str(profile.get("bindingness") or "unclear"),
        },
        "answers": answers,
    }


def run_agreement_analysis(
    document: dict[str, Any],
    model_key: str,
    registry_path: str | Path = "config/models/model_registry.yaml",
    question_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mapping = question_map or load_question_map()
    registry = load_model_registry(registry_path)
    model_config = resolve_runtime_model_config(get_model_config(registry, model_key))
    if model_config.provider not in {"openai_compatible", "gemini"}:
        raise ValueError("Agreement analysis requires a configured external AI model.")
    request = build_analysis_request(document, model_config.model_name, mapping)
    response = build_provider(model_config).complete(request)
    result = _normalise_result(
        document,
        _json_payload(response.content, response.structured_output),
        mapping,
    )
    created_at = datetime.now(timezone.utc).isoformat()
    return {
        "analysis_id": f"{document['document_id']}:{created_at}",
        "document_id": document["document_id"],
        "document_filename": document.get("original_filename"),
        "status": "provisional",
        "profile": result["profile"],
        "answers": result["answers"],
        "model_name": response.model,
        "model_provider": response.provider,
        "prompt_version": PROMPT_VERSION,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "created_at": created_at,
    }


def initialize_analysis_table(db_path: Path = DEFAULT_WORKSPACE_DB_PATH) -> Path:
    resolved = initialize_workspace_db(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS agreement_automatic_analyses (
                analysis_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    return resolved


def save_agreement_analysis(
    analysis: dict[str, Any], db_path: Path = DEFAULT_WORKSPACE_DB_PATH
) -> None:
    if uses_persistent_store(db_path):
        upsert_record(COLLECTION, analysis["analysis_id"], analysis)
        return
    resolved = initialize_analysis_table(db_path)
    with sqlite3.connect(resolved) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO agreement_automatic_analyses VALUES (?, ?, ?, ?)",
            (
                analysis["analysis_id"],
                analysis["document_id"],
                json.dumps(analysis, ensure_ascii=False),
                analysis["created_at"],
            ),
        )


def load_agreement_analyses(
    db_path: Path = DEFAULT_WORKSPACE_DB_PATH,
) -> list[dict[str, Any]]:
    if uses_persistent_store(db_path):
        return load_records(COLLECTION)
    resolved = initialize_analysis_table(db_path)
    with sqlite3.connect(resolved) as connection:
        rows = connection.execute(
            "SELECT payload FROM agreement_automatic_analyses ORDER BY created_at DESC"
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def latest_analysis_by_document(
    analyses: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for analysis in sorted(analyses, key=lambda item: item.get("created_at", ""), reverse=True):
        latest.setdefault(str(analysis.get("document_id")), analysis)
    return latest
