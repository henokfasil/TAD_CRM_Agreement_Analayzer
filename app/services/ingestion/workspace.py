from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from app.schemas.documents import ExtractionResult, StoredDocument


def build_document_record(
    stored: StoredDocument,
    extraction: ExtractionResult | None,
) -> dict[str, Any]:
    pages = []
    if extraction is not None:
        pages = [
            {
                "page_number": page.page_number,
                "text": page.text,
                "extraction_confidence": page.extraction_confidence,
            }
            for page in extraction.pages
        ]

    return {
        "document_id": stored.sha256_hash,
        "original_filename": stored.original_filename,
        "stored_path": str(stored.stored_path),
        "sha256_hash": stored.sha256_hash,
        "size_bytes": stored.size_bytes,
        "duplicate": stored.duplicate,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "extraction_method": extraction.method if extraction else None,
        "parser_version": extraction.parser_version if extraction else None,
        "page_count": len(pages),
        "pages": pages,
    }


def upsert_document_record(
    records: list[dict[str, Any]],
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    kept = [item for item in records if item["document_id"] != record["document_id"]]
    return [record, *kept]


def records_to_json(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, indent=2, ensure_ascii=False)


def pages_to_csv(records: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "document_id",
            "original_filename",
            "sha256_hash",
            "page_number",
            "text",
        ],
    )
    writer.writeheader()
    for record in records:
        for page in record.get("pages", []):
            writer.writerow(
                {
                    "document_id": record["document_id"],
                    "original_filename": record["original_filename"],
                    "sha256_hash": record["sha256_hash"],
                    "page_number": page["page_number"],
                    "text": page["text"],
                }
            )
    return output.getvalue()

