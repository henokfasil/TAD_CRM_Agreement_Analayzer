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

    profiles = [{"agreement_id": "a1", "canonical_title": "Critical Minerals Partnership"}]
    ai_proposals = [{"proposal_id": "a1", "variable_code": "mech_work_group"}]
    verification_results = [{"verification_id": "v1", "support_status": "supports"}]
    adjudications = [{"adjudication_id": "adj1", "final_value": "1"}]
    summary = build_workspace_summary(
        records,
        decisions,
        profiles,
        ai_proposals,
        verification_results,
        adjudications,
    )
    bundle = build_research_export_bundle(
        records,
        decisions,
        profiles,
        ai_proposals,
        verification_results,
        adjudications,
    )

    assert summary["agreement_profiles"] == 1
    assert summary["documents"] == 1
    assert summary["manual_coding_decisions"] == 1
    assert summary["ai_coding_proposals"] == 1
    assert summary["verification_results"] == 1
    assert summary["adjudicated_decisions"] == 1
    assert len(build_candidate_provisions(records)) == 1
    assert "mech_work_group" in bundle["manual_decisions_csv"]
    assert "Critical Minerals Partnership" in bundle["agreement_profiles_csv"]
    assert "mech_work_group" in bundle["ai_proposals_csv"]
    assert "supports" in bundle["verification_results_csv"]
    assert "adj1" in bundle["adjudications_csv"]
    assert "candidate_provisions" in bundle["summary_json"]
