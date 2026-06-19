from app.services.reporting.exports import (
    build_candidate_provisions,
    build_research_export_bundle,
    build_workspace_summary,
)


def test_reporting_bundle_contains_workspace_outputs() -> None:
    records = [
        {
            "document_id": "doc1",
            "original_filename": "agreement.pdf",
            "sha256_hash": "doc1",
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "text": (
                        "The Parties intend to establish a working group on critical minerals. "
                        "The group will monitor implementation and report progress."
                    ),
                }
            ],
        }
    ]
    decisions = [
        {
            "decision_id": "d1",
            "document_id": "doc1",
            "provision_id": "p1",
            "variable_code": "mech_work_group",
            "proposed_value": "1",
            "reviewer_status": "provisional",
            "evidence_page": 1,
            "evidence_quote": "working group",
            "reviewer_note": "",
            "created_at": "2026-06-19T00:00:00+00:00",
        }
    ]

    summary = build_workspace_summary(records, decisions)
    bundle = build_research_export_bundle(records, decisions)

    assert summary["documents"] == 1
    assert summary["manual_coding_decisions"] == 1
    assert len(build_candidate_provisions(records)) == 1
    assert "mech_work_group" in bundle["manual_decisions_csv"]
    assert "candidate_provisions" in bundle["summary_json"]
