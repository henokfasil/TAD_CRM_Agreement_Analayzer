from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.review.adjudication import (
    adjudications_to_csv,
    build_adjudication_decision,
    load_adjudication_decisions,
    save_adjudication_decision,
)


def test_adjudication_roundtrip_from_ai_source() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_adjudication_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    source = {
        "proposal_id": "proposal1",
        "document_id": "doc1",
        "provision_id": "prov1",
        "variable_code": "inv_gen_ref",
    }

    decision = build_adjudication_decision(
        source_type="ai",
        source=source,
        final_value="1",
        rationale="Evidence supports a final positive value.",
        adjudicator_id="tester",
    )
    save_adjudication_decision(decision, db_path)
    decisions = load_adjudication_decisions(db_path)

    assert decisions[0]["validation_status"] == "adjudicated"
    assert decisions[0]["source_type"] == "ai"
    assert "Evidence supports" in adjudications_to_csv(decisions)
