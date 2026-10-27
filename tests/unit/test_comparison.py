from app.services.reporting.comparison import (
    build_classification_comparison,
    build_document_overview,
    build_text_comparison,
    shared_classification_summary,
)


def _record(document_id: str, filename: str) -> dict:
    return {
        "document_id": document_id,
        "original_filename": filename,
        "page_count": 1,
        "extraction_method": "pymupdf",
        "pages": [
            {
                "page_number": 1,
                "text": (
                    "Article 1\nThe parties cooperate on recycling, recovery, responsible "
                    "sourcing, research, innovation, and sustainable raw-material value chains."
                ),
            }
        ],
    }


def test_document_comparison_works_without_adjudications() -> None:
    overview = build_document_overview([_record("a", "A.pdf"), _record("b", "B.pdf")])
    assert [row["agreement"] for row in overview] == ["A.pdf", "B.pdf"]
    assert all(row["candidate_provisions"] >= 1 for row in overview)


def test_human_approved_value_takes_precedence() -> None:
    records = [_record("a", "A.pdf"), _record("b", "B.pdf")]
    proposals = [
        {"document_id": "a", "variable_code": "recycling", "proposed_value": "No"},
        {"document_id": "b", "variable_code": "recycling", "proposed_value": "Yes"},
    ]
    adjudications = [
        {"document_id": "a", "variable_code": "recycling", "final_value": "Yes"}
    ]
    rows = build_classification_comparison(records, adjudications, [], proposals)
    assert len(shared_classification_summary(rows)) == 2
    a_row = next(row for row in rows if row["agreement"] == "A.pdf")
    assert a_row["value"] == "Yes"
    assert a_row["status"] == "Human-approved"


def test_text_comparison_finds_themes_overlap_and_evidence() -> None:
    records = [_record("a", "A.pdf"), _record("b", "B.pdf")]
    result = build_text_comparison(records)
    raw_materials = next(row for row in result["themes"] if row["theme"] == "Raw-material value chains")
    assert raw_materials["A.pdf"] > 0
    assert raw_materials["B.pdf"] > 0
    assert result["pairwise"][0]["shared_vocabulary_percent"] > 0
    assert result["evidence"]["Recycling and circularity"]["A.pdf"][0]["page"] == 1
