from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.storage.schema import CURRENT_SCHEMA_VERSION, get_schema_status, initialize_application_schema


def test_initialize_application_schema_records_version_and_tables() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_schema_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"

    resolved = initialize_application_schema(db_path)
    status = get_schema_status(db_path)

    assert resolved == db_path
    assert status["current_schema_version"] == CURRENT_SCHEMA_VERSION
    assert "documents" in status["tables"]
    assert "agreement_profiles" in status["tables"]
    assert "manual_coding_decisions" in status["tables"]
    assert status["applied_versions"][0]["version"] == CURRENT_SCHEMA_VERSION
