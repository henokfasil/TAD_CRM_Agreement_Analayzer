from pathlib import Path
import tempfile
from uuid import uuid4

from app.services.agreements.profiles import (
    agreement_profiles_to_csv,
    build_agreement_profile,
    link_document_to_agreement,
    load_agreement_document_links,
    load_agreement_profiles,
    save_agreement_profile,
)


def test_agreement_profile_roundtrip_and_document_link() -> None:
    runtime = Path(tempfile.gettempdir()) / "crm_agreement_profile_tests" / str(uuid4())
    db_path = runtime / "workspace.sqlite"
    profile = build_agreement_profile(
        canonical_title="Critical Minerals Partnership",
        short_title="CMP",
        agreement_type="MoU",
        parties="A; B",
    )

    save_agreement_profile(profile, db_path)
    link_document_to_agreement(profile["agreement_id"], "doc1", db_path)

    profiles = load_agreement_profiles(db_path)
    links = load_agreement_document_links(db_path)

    assert profiles[0]["canonical_title"] == "Critical Minerals Partnership"
    assert links[0]["document_id"] == "doc1"
    assert "Critical Minerals Partnership" in agreement_profiles_to_csv(profiles)

