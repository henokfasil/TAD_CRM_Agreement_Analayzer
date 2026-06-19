from pathlib import Path
import tempfile
from uuid import uuid4

from app.schemas.codebook import CodebookVariableSchema
from app.services.classification.ai_coding import (
    ai_proposals_to_csv,
    load_ai_coding_proposals,
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
