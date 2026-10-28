from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.research.answer_sheet import (
    build_agreement_approval,
    build_answer_sheet,
    build_question_review,
    load_agreement_approvals,
    load_question_map,
    load_question_reviews,
    save_agreement_approval,
    save_question_review,
)
from app.services.reporting.comparison import build_research_question_comparison


def test_question_map_contains_nine_research_questions() -> None:
    mapping = load_question_map()

    assert len(mapping["questions"]) == 9
    assert mapping["questions"][-1]["id"] == "local_value_addition"


def test_answer_sheet_combines_profile_coding_and_evidence() -> None:
    proposal = {
        "proposal_id": "proposal-1",
        "document_id": "doc-1",
        "provision_id": "provision-1",
        "variable_code": "inv_gen_ref",
        "proposed_value": "1",
        "evidence_page": 4,
        "evidence_quote": "The parties intend to mobilise investment.",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    adjudication = {
        "adjudication_id": "adj-1",
        "source_id": "proposal-1",
        "document_id": "doc-1",
        "variable_code": "inv_gen_ref",
        "final_value": "1",
        "created_at": "2026-01-02T00:00:00+00:00",
    }
    answers = build_answer_sheet(
        document_id="doc-1",
        profiles=[
            {
                "agreement_id": "agreement-1",
                "countries": ["Country A", "Country B"],
                "organisations": ["Regional Union"],
                "bindingness_status": "non-binding",
            }
        ],
        links=[{"agreement_id": "agreement-1", "document_id": "doc-1"}],
        adjudications=[adjudication],
        manual_decisions=[],
        ai_proposals=[proposal],
        reviews=[],
    )

    assert len(answers) == 9
    assert answers[0]["answer"] == "Yes"
    assert "Country A" in answers[0]["summary"]
    investment = next(item for item in answers if item["question_id"] == "investment_financing")
    assert investment["answer"] == "Yes"
    assert investment["evidence"][0]["page"] == 4


def test_question_reviews_and_profile_approval_roundtrip() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_answer_sheet_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    review = build_question_review(
        "doc-1",
        "participants",
        "Yes",
        "Country A participates.",
        "The official text names Country A.",
        "reviewer",
    )
    approval = build_agreement_approval(
        "doc-1",
        "reviewer",
        "All nine answers were checked.",
    )

    save_question_review(review, db_path)
    save_agreement_approval(approval, db_path)

    assert load_question_reviews(db_path)[0]["final_answer"] == "Yes"
    assert load_agreement_approvals(db_path)[0]["validation_status"] == "approved"

    updated_review = build_question_review(
        "doc-1",
        "participants",
        "Mixed",
        "Country A and an organisation participate.",
        "The answer was refined after approval.",
        "reviewer",
    )
    save_question_review(updated_review, db_path)
    assert load_agreement_approvals(db_path)[0]["validation_status"] == "needs_reapproval"


def test_only_approved_profiles_enter_question_comparison() -> None:
    rows = build_research_question_comparison(
        records=[
            {"document_id": "approved-doc", "original_filename": "Approved.pdf"},
            {"document_id": "draft-doc", "original_filename": "Draft.pdf"},
        ],
        question_reviews=[
            {
                "document_id": "approved-doc",
                "question_id": "participants",
                "final_answer": "Yes",
                "final_summary": "Country A participates.",
                "validation_status": "validated",
            },
            {
                "document_id": "draft-doc",
                "question_id": "participants",
                "final_answer": "Yes",
                "final_summary": "Country B participates.",
                "validation_status": "validated",
            },
        ],
        approvals=[
            {
                "document_id": "approved-doc",
                "validation_status": "approved",
            }
        ],
    )

    assert rows[0]["Approved.pdf"].startswith("Yes")
    assert rows[0]["Draft.pdf"] == "Not approved"
