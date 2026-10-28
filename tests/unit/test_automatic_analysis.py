from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.research.automatic_analysis import (
    _normalise_result,
    latest_analysis_by_document,
    load_agreement_analyses,
    save_agreement_analysis,
)
from app.services.research.answer_sheet import build_answer_sheet, load_question_map


def _document() -> dict:
    return {
        "document_id": "doc-1",
        "original_filename": "Agreement.pdf",
        "page_count": 2,
        "pages": [
            {
                "page_number": 1,
                "text": "The European Union and Chile establish a working group.",
            },
            {
                "page_number": 2,
                "text": "The participants intend to mobilise investment for local processing.",
            },
        ],
    }


def test_automatic_analysis_checks_quotes_and_supplies_all_questions() -> None:
    mapping = load_question_map()
    payload = {
        "profile": {
            "countries": ["Chile"],
            "organisations": ["European Union"],
            "bindingness": "non-binding",
        },
        "answers": [
            {
                "question_id": "institutions_monitoring",
                "answer": "Yes",
                "summary": "A working group is established.",
                "confidence": 0.9,
                "evidence": [{"page": 99, "quote": "establish a working group"}],
            },
            {
                "question_id": "trade",
                "answer": "Yes",
                "summary": "A fabricated claim.",
                "confidence": 0.9,
                "evidence": [{"page": 1, "quote": "quotation not in document"}],
            },
        ],
    }

    result = _normalise_result(_document(), payload, mapping)

    assert len(result["answers"]) == 9
    institutions = next(
        answer for answer in result["answers"] if answer["question_id"] == "institutions_monitoring"
    )
    assert institutions["evidence"][0]["page"] == 1
    trade = next(answer for answer in result["answers"] if answer["question_id"] == "trade")
    assert trade["answer"] == "Unclear"
    assert trade["confidence"] == 0.35


def test_analysis_roundtrip_and_answer_sheet_integration() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_automatic_analysis_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    analysis = {
        "analysis_id": "analysis-1",
        "document_id": "doc-1",
        "created_at": "2026-10-28T10:00:00+00:00",
        "profile": {"countries": ["Chile"], "organisations": ["European Union"]},
        "answers": [
            {
                "question_id": "participants",
                "answer": "Yes",
                "summary": "Chile and the European Union participate.",
                "evidence": [{"page": 1, "quote": "The European Union and Chile"}],
            }
        ],
    }
    save_agreement_analysis(analysis, db_path)
    loaded = load_agreement_analyses(db_path)

    assert latest_analysis_by_document(loaded)["doc-1"]["analysis_id"] == "analysis-1"
    answers = build_answer_sheet(
        document_id="doc-1",
        profiles=[],
        links=[],
        adjudications=[],
        manual_decisions=[],
        ai_proposals=[],
        reviews=[],
        automatic_analyses=loaded,
    )
    assert answers[0]["answer"] == "Yes"
    assert answers[0]["evidence"][0]["page"] == 1
