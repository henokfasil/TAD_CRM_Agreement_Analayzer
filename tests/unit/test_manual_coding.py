from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.review.manual_coding import (
    build_manual_decision,
    decisions_to_csv,
    load_manual_decisions,
    save_manual_decision,
)


def test_manual_coding_roundtrip() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_manual_coding_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    provision = {
        "provision_id": "prov1",
        "page_start": 3,
        "provision_text": "The Parties shall cooperate on critical minerals.",
    }
    decision = build_manual_decision(
        document_id="doc1",
        provision=provision,
        variable_code="inv_gen_ref",
        proposed_value="1",
        reviewer_status="provisional",
        evidence_quote=provision["provision_text"],
        reviewer_note="Initial manual coding.",
    )

    save_manual_decision(decision, db_path)
    decisions = load_manual_decisions(db_path)

    assert len(decisions) == 1
    assert decisions[0]["variable_code"] == "inv_gen_ref"
    assert decisions[0]["evidence_page"] == 3
    assert "Initial manual coding" in decisions_to_csv(decisions)
