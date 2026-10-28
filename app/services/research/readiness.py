from __future__ import annotations

from typing import Any


FINAL_STATUSES = {"validated", "final", "approved"}


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "pending"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _reporting_date(profile: dict[str, Any]) -> str:
    return str(profile.get("signature_date") or profile.get("entry_into_force_date") or "")


def _participants(profile: dict[str, Any]) -> list[str]:
    structured = list(profile.get("countries") or []) + list(profile.get("organisations") or [])
    if structured:
        return structured
    legacy = str(profile.get("parties") or "")
    return [item.strip() for item in legacy.split(";") if item.strip()]


def research_record(profile: dict[str, Any], validated_coding: bool = False) -> dict[str, Any]:
    """Normalise one profile into the fields used by analysis specifications."""
    return {
        **profile,
        "reporting_date": _reporting_date(profile),
        "participants": _participants(profile),
        "validated_coding": validated_coding,
    }


def build_research_readiness(
    profiles: list[dict[str, Any]],
    records: list[dict[str, Any]],
    links: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    specification: dict[str, Any],
) -> dict[str, Any]:
    """Assess corpus readiness without generating or imitating publication figures."""
    linked_agreements = {str(link.get("agreement_id")) for link in links}
    coded_agreements = {str(item.get("document_id")) for item in adjudications}
    linked_document_by_agreement = {
        str(link.get("agreement_id")): str(link.get("document_id")) for link in links
    }

    included_profiles = [
        profile
        for profile in profiles
        if str(profile.get("inclusion_status", "pending")).lower() != "excluded"
    ]
    normalised = []
    for profile in included_profiles:
        agreement_id = str(profile.get("agreement_id", ""))
        document_id = linked_document_by_agreement.get(agreement_id, "")
        normalised.append(research_record(profile, document_id in coded_agreements))

    analysis_rows = []
    for analysis in specification.get("analysis_registry", []):
        required_fields = list(analysis.get("required_fields", []))
        complete = [
            row for row in normalised if all(_has_value(row.get(field)) for field in required_fields)
        ]
        validated = [
            row
            for row in complete
            if str(row.get("validation_status", "provisional")).lower() in FINAL_STATUSES
        ]
        minimum = int(analysis.get("minimum_records", 1))
        if len(validated) >= minimum and len(validated) == len(normalised) and normalised:
            readiness = "Publication ready"
        elif len(complete) >= minimum:
            readiness = "Exploratory only"
        else:
            readiness = "Missing metadata"
        analysis_rows.append(
            {
                "analysis_id": analysis.get("id"),
                "reference": analysis.get("reference"),
                "analysis": analysis.get("title"),
                "required_fields": ", ".join(required_fields),
                "complete_records": len(complete),
                "validated_records": len(validated),
                "corpus_records": len(normalised),
                "readiness": readiness,
                "implementation": analysis.get("status", "planned"),
            }
        )

    core_fields = (
        "canonical_title",
        "agreement_type",
        "reporting_date",
        "participants",
        "bindingness_status",
        "metadata_sources",
    )
    core_complete = [
        row for row in normalised if all(_has_value(row.get(field)) for field in core_fields)
    ]
    validated_profiles = [
        row
        for row in normalised
        if str(row.get("validation_status", "provisional")).lower() in FINAL_STATUSES
    ]
    return {
        "specification_version": specification.get("version"),
        "documents": len(records),
        "agreement_profiles": len(profiles),
        "included_corpus": len(normalised),
        "linked_profiles": sum(
            1 for profile in included_profiles if str(profile.get("agreement_id")) in linked_agreements
        ),
        "core_metadata_complete": len(core_complete),
        "validated_profiles": len(validated_profiles),
        "adjudicated_decisions": len(adjudications),
        "analysis_rows": analysis_rows,
        "publication_ready": bool(normalised)
        and len(core_complete) == len(normalised)
        and len(validated_profiles) == len(normalised),
    }
