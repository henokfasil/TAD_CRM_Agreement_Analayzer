from pathlib import Path
import tempfile
from uuid import uuid4

from app.schemas.codebook import CodebookVariableSchema
from app.services.classification.ai_coding import (
    ai_proposals_to_csv,
    load_ai_coding_proposals,
    run_batch_ai_coding_proposals,
    run_ai_coding_proposal,
    save_ai_coding_proposal,
)


def test_ai_coding_proposal_roundtrip_uses_mock_provider() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_ai_coding_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    variable = CodebookVariableSchema(
        code="inv_gen_ref",
        family="investment",
        label="Investment",
        description="General investment reference",
        data_type="binary",
        allowed_values=[0, 1],
    )
    provision = {
        "provision_id": "prov1",
        "page_start": 2,
        "provision_text": "The Parties shall cooperate on critical minerals investment.",
        "segmentation_version": "basic_v1",
    }

    proposal = run_ai_coding_proposal(
        document_id="doc1",
        provision=provision,
        variable=variable,
        existing_decisions=[],
        codebook_version="v1",
    )
    save_ai_coding_proposal(proposal, db_path)
    proposals = load_ai_coding_proposals(db_path)

    assert proposals[0]["model_provider"] == "mock"
    assert proposals[0]["reviewer_status"] == "pending"
    assert proposals[0]["verification_status"] == "not_verified"
    assert "inv_gen_ref" in ai_proposals_to_csv(proposals)


def test_batch_ai_coding_skips_existing_model_variable_pairs() -> None:
    variable = CodebookVariableSchema(
        code="inv_gen_ref",
        family="investment",
        label="Investment",
        description="General investment reference",
        data_type="binary",
        allowed_values=[0, 1],
    )
    provisions = [
        {
            "provision_id": "prov1",
            "page_start": 1,
            "provision_text": "The Parties shall cooperate on critical minerals investment.",
            "segmentation_version": "basic_v1",
        },
        {
            "provision_id": "prov2",
            "page_start": 2,
            "provision_text": "This memorandum records future dialogue.",
            "segmentation_version": "basic_v1",
        },
    ]
    existing_proposals = [
        {
            "document_id": "doc1",
            "provision_id": "prov1",
            "variable_code": "inv_gen_ref",
            "model_provider": "mock",
            "model_name": "mock-coding-v1",
        }
    ]

    result = run_batch_ai_coding_proposals(
        document_id="doc1",
        provisions=provisions,
        variable=variable,
        existing_decisions=[],
        existing_proposals=existing_proposals,
        codebook_version="v1",
        limit=2,
        skip_existing=True,
    )

    assert len(result["created"]) == 1
    assert result["created"][0]["provision_id"] == "prov2"
    assert len(result["skipped"]) == 1
    assert result["skipped"][0]["provision_id"] == "prov1"
    assert result["errors"] == []
