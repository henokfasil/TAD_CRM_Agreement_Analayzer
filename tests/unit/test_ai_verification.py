from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.verification.ai_verification import (
    load_verification_results,
    run_mock_verification,
    save_verification_result,
    verification_results_to_csv,
)


def test_mock_verification_flags_rule_conflict_and_roundtrips() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_ai_verification_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    proposal = {
        "proposal_id": "p1",
        "proposed_value": "1",
        "evidence_quote": "The Parties shall cooperate.",
        "rule_status": "violation",
    }

    result = run_mock_verification(proposal)
    save_verification_result(result, db_path)
    results = load_verification_results(db_path)

    assert results[0]["support_status"] == "does_not_support"
    assert results[0]["human_review_required"] is True
    assert "dependency conflict" in results[0]["critique"]
    assert "mock-verifier-v1" in verification_results_to_csv(results)
