from app.services.research.readiness import build_research_readiness
from app.services.research.specification import load_report_specification


def test_report_specification_loads_analysis_contracts() -> None:
    specification = load_report_specification()

    assert specification["version"] == "report-spec-v1"
    assert len(specification["analysis_registry"]) >= 6
    assert specification["publication_rules"]["require_page_evidence_for_coded_claims"]


def test_readiness_distinguishes_complete_and_validated_records() -> None:
    specification = load_report_specification()
    profiles = [
        {
            "agreement_id": "agreement-1",
            "canonical_title": "A-B CRM partnership",
            "agreement_type": "MoU",
            "signature_date": "2025-01-15",
            "countries": ["A", "B"],
            "organisations": [],
            "bindingness_status": "non-binding",
            "g7_participation": "yes",
            "global_south_participation": "yes",
            "producer_consumer_pair": "producer-consumer",
            "metadata_sources": "Official text; classification source",
            "inclusion_status": "included",
            "validation_status": "validated",
        }
    ]
    readiness = build_research_readiness(
        profiles=profiles,
        records=[{"document_id": "document-1"}],
        links=[{"agreement_id": "agreement-1", "document_id": "document-1"}],
        adjudications=[{"document_id": "document-1", "variable_code": "inv_gen_ref"}],
        specification=specification,
    )

    assert readiness["publication_ready"] is True
    assert readiness["core_metadata_complete"] == 1
    assert readiness["validated_profiles"] == 1
    assert all(row["validated_records"] == 1 for row in readiness["analysis_rows"])


def test_readiness_blocks_incomplete_provisional_records() -> None:
    specification = load_report_specification()
    readiness = build_research_readiness(
        profiles=[
            {
                "agreement_id": "agreement-1",
                "canonical_title": "Incomplete agreement",
                "agreement_type": "",
                "countries": [],
                "inclusion_status": "pending",
                "validation_status": "provisional",
            }
        ],
        records=[],
        links=[],
        adjudications=[],
        specification=specification,
    )

    assert readiness["publication_ready"] is False
    assert readiness["core_metadata_complete"] == 0
    assert readiness["validated_profiles"] == 0
