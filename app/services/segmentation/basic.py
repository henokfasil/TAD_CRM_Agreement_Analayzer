from __future__ import annotations

import csv
import hashlib
import io
import re
from typing import Any

SEGMENTATION_VERSION = "basic_v1"
MIN_SEGMENT_CHARS = 80

HEADING_PATTERN = re.compile(
    r"(?im)^(?P<heading>(article|section|chapter|annex|part)\s+"
    r"(?P<number>[0-9ivxlcdm]+[a-z]?|[a-z])(?:[.: -]+(?P<title>.+))?)$"
)


def _normalise_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _stable_id(document_id: str, page_number: int, ordinal: int, text: str) -> str:
    payload = f"{document_id}:{page_number}:{ordinal}:{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _paragraph_segments(text: str) -> list[str]:
    normalised = text.replace("\r\n", "\n")
    blocks = [block.strip() for block in re.split(r"\n\s*\n+", normalised) if block.strip()]
    if len(blocks) <= 1:
        blocks = [block.strip() for block in re.split(r"(?<=[.;:])\s+(?=[A-Z0-9(])", normalised) if block.strip()]
    segments = [_normalise_text(block) for block in blocks if len(_normalise_text(block)) >= MIN_SEGMENT_CHARS]
    if not segments and len(_normalise_text(normalised)) >= MIN_SEGMENT_CHARS:
        return [_normalise_text(normalised)]
    return segments


def segment_page(
    document_id: str,
    page_number: int,
    text: str,
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    headings = list(HEADING_PATTERN.finditer(text))

    if headings:
        for ordinal, match in enumerate(headings, start=1):
            start = match.end()
            end = headings[ordinal].start() if ordinal < len(headings) else len(text)
            provision_text = _normalise_text(text[start:end])
            if len(provision_text) < MIN_SEGMENT_CHARS:
                continue
            heading = _normalise_text(match.group("heading"))
            article_number = match.group("number")
            title = match.group("title")
            segments.append(
                {
                    "provision_id": _stable_id(document_id, page_number, ordinal, provision_text),
                    "document_id": document_id,
                    "page_start": page_number,
                    "page_end": page_number,
                    "article_number": article_number,
                    "section_title": _normalise_text(title) if title else heading,
                    "provision_text": provision_text,
                    "segmentation_version": SEGMENTATION_VERSION,
                    "segmentation_method": "heading",
                }
            )

    if segments:
        return segments

    return [
        {
            "provision_id": _stable_id(document_id, page_number, ordinal, segment),
            "document_id": document_id,
            "page_start": page_number,
            "page_end": page_number,
            "article_number": None,
            "section_title": None,
            "provision_text": segment,
            "segmentation_version": SEGMENTATION_VERSION,
            "segmentation_method": "paragraph",
        }
        for ordinal, segment in enumerate(_paragraph_segments(text), start=1)
    ]


def segment_document_pages(record: dict[str, Any]) -> list[dict[str, Any]]:
    provisions: list[dict[str, Any]] = []
    for page in record.get("pages", []):
        provisions.extend(
            segment_page(
                document_id=record["document_id"],
                page_number=page["page_number"],
                text=page["text"],
            )
        )
    return provisions


def provisions_to_csv(provisions: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "provision_id",
            "document_id",
            "page_start",
            "page_end",
            "article_number",
            "section_title",
            "segmentation_method",
            "segmentation_version",
            "provision_text",
        ],
    )
    writer.writeheader()
    for provision in provisions:
        writer.writerow({field: provision.get(field) for field in writer.fieldnames})
    return output.getvalue()
