from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.segmentation.basic import segment_document_pages


def build_document_overview(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        pages = record.get("pages", [])
        text = " ".join(str(page.get("text", "")) for page in pages)
        rows.append(
            {
                "document_id": record["document_id"],
                "agreement": record["original_filename"],
                "pages": record.get("page_count", len(pages)),
                "candidate_provisions": len(segment_document_pages(record)),
                "extracted_characters": len(text.strip()),
                "extraction_method": record.get("extraction_method") or "unknown",
            }
        )
    return rows


def build_classification_comparison(
    records: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    manual_decisions: list[dict[str, Any]],
    ai_proposals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build one comparable row per document/variable, preferring reviewed evidence."""
    filenames = {record["document_id"]: record["original_filename"] for record in records}
    selected: dict[tuple[str, str], dict[str, Any]] = {}

    sources = (
        (1, "AI proposal", ai_proposals, "proposed_value"),
        (2, "Manual classification", manual_decisions, "proposed_value"),
        (3, "Human-approved", adjudications, "final_value"),
    )
    for priority, status, items, value_field in sources:
        for item in items:
            document_id = str(item.get("document_id", ""))
            variable_code = str(item.get("variable_code", ""))
            if document_id not in filenames or not variable_code:
                continue
            key = (document_id, variable_code)
            current = selected.get(key)
            if current and current["_priority"] > priority:
                continue
            selected[key] = {
                "_priority": priority,
                "agreement": filenames[document_id],
                "variable": variable_code,
                "value": item.get(value_field, ""),
                "status": status,
                "evidence_page": item.get("evidence_page"),
                "evidence": item.get("evidence_quote", ""),
            }

    return [
        {key: value for key, value in row.items() if key != "_priority"}
        for row in sorted(selected.values(), key=lambda row: (row["variable"], row["agreement"]))
    ]


def shared_classification_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row["variable"]) for row in rows)
    return [row for row in rows if counts[str(row["variable"])] > 1]
