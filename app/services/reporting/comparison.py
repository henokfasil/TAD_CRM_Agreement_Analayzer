from __future__ import annotations

from collections import Counter
from itertools import combinations
import re
from typing import Any

from app.services.segmentation.basic import segment_document_pages

THEMES = {
    "Raw-material value chains": ("raw material", "critical mineral", "value chain"),
    "Investment and finance": ("investment", "finance", "funding", "financial"),
    "Research and innovation": ("research", "innovation", "technology", "scientific"),
    "Environmental and ESG standards": (
        "environmental",
        "sustainability",
        "sustainable",
        "governance",
        "responsible mining",
    ),
    "Recycling and circularity": ("recycling", "recycle", "circular", "recovery"),
    "Skills and capacity building": ("skills", "training", "capacity building", "education"),
    "Data and geological knowledge": ("geological", "data sharing", "digital", "mapping"),
    "Batteries": ("battery", "batteries"),
    "Renewable hydrogen": ("hydrogen",),
}

STOPWORDS = {
    "about", "after", "also", "among", "been", "between", "both", "could", "each",
    "from", "have", "into", "more", "other", "shall", "should", "such", "than", "that",
    "their", "there", "these", "they", "this", "through", "under", "which", "will", "with",
    "would", "european", "union", "parties", "partnership", "cooperation", "agreement",
}


def _document_text(record: dict[str, Any]) -> str:
    return "\n".join(str(page.get("text", "")) for page in record.get("pages", []))


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z-]{3,}", text.lower())
        if token not in STOPWORDS
    }


def build_text_comparison(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Create an exploratory comparison directly from extracted agreement text."""
    texts = {record["document_id"]: _document_text(record) for record in records}
    token_sets = {document_id: _tokens(text) for document_id, text in texts.items()}
    pairwise = []
    for left, right in combinations(records, 2):
        left_tokens = token_sets[left["document_id"]]
        right_tokens = token_sets[right["document_id"]]
        union = left_tokens | right_tokens
        similarity = len(left_tokens & right_tokens) / len(union) if union else 0
        pairwise.append(
            {
                "agreement_a": left["original_filename"],
                "agreement_b": right["original_filename"],
                "shared_vocabulary_percent": round(similarity * 100, 1),
                "shared_terms": ", ".join(sorted(left_tokens & right_tokens)[:20]),
            }
        )

    theme_rows = []
    evidence: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for theme, keywords in THEMES.items():
        row: dict[str, Any] = {"theme": theme}
        evidence[theme] = {}
        for record in records:
            filename = record["original_filename"]
            matches: list[dict[str, Any]] = []
            total = 0
            for page in record.get("pages", []):
                text = str(page.get("text", ""))
                lower = text.lower()
                page_hits = sum(lower.count(keyword) for keyword in keywords)
                total += page_hits
                if page_hits and len(matches) < 3:
                    sentences = re.split(r"(?<=[.!?;])\s+|\n+", text)
                    excerpt = next(
                        (sentence.strip() for sentence in sentences if any(k in sentence.lower() for k in keywords)),
                        text[:400].strip(),
                    )
                    matches.append(
                        {"page": page.get("page_number"), "excerpt": excerpt[:500]}
                    )
            row[filename] = total
            evidence[theme][filename] = matches
        theme_rows.append(row)

    frequencies: dict[str, Counter[str]] = {
        record["document_id"]: Counter(
            token
            for token in re.findall(r"[a-z][a-z-]{3,}", texts[record["document_id"]].lower())
            if token not in STOPWORDS
        )
        for record in records
    }
    distinctive_terms = {}
    for record in records:
        own = frequencies[record["document_id"]]
        others = set().union(
            *(token_sets[other["document_id"]] for other in records if other is not record)
        )
        distinctive = [(term, count) for term, count in own.most_common() if term not in others][:12]
        distinctive_terms[record["original_filename"]] = ", ".join(term for term, _ in distinctive)

    return {
        "pairwise": pairwise,
        "themes": theme_rows,
        "evidence": evidence,
        "distinctive_terms": distinctive_terms,
    }


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
