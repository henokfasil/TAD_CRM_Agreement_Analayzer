from __future__ import annotations

import json
from collections import Counter
from typing import Any

from app.services.ingestion.workspace import pages_to_csv
from app.services.review.manual_coding import decisions_to_csv
from app.services.segmentation.basic import provisions_to_csv, segment_document_pages
from app.services.agreements.profiles import agreement_profiles_to_csv
from app.services.classification.ai_coding import ai_proposals_to_csv
from app.services.verification.ai_verification import verification_results_to_csv


def build_candidate_provisions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    provisions: list[dict[str, Any]] = []
    for record in records:
        provisions.extend(segment_document_pages(record))
    return provisions


def build_workspace_summary(
    records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    profiles: list[dict[str, Any]] | None = None,
    ai_proposals: list[dict[str, Any]] | None = None,
    verification_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    provisions = build_candidate_provisions(records)
    reviewer_status_counts = Counter(decision["reviewer_status"] for decision in decisions)
    variable_counts = Counter(decision["variable_code"] for decision in decisions)
    return {
        "agreement_profiles": len(profiles or []),
        "documents": len(records),
        "pages": sum(record.get("page_count", 0) for record in records),
        "candidate_provisions": len(provisions),
        "manual_coding_decisions": len(decisions),
        "ai_coding_proposals": len(ai_proposals or []),
        "verification_results": len(verification_results or []),
        "reviewer_status_counts": dict(sorted(reviewer_status_counts.items())),
        "coded_variable_counts": dict(sorted(variable_counts.items())),
    }


def build_research_export_bundle(
    records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    profiles: list[dict[str, Any]] | None = None,
    ai_proposals: list[dict[str, Any]] | None = None,
    verification_results: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    provisions = build_candidate_provisions(records)
    agreement_profiles = profiles or []
    proposal_records = ai_proposals or []
    verifier_records = verification_results or []
    summary = build_workspace_summary(records, decisions, agreement_profiles, proposal_records, verifier_records)
    return {
        "summary_json": json.dumps(summary, indent=2, ensure_ascii=False),
        "agreement_profiles_csv": agreement_profiles_to_csv(agreement_profiles),
        "documents_json": json.dumps(records, indent=2, ensure_ascii=False),
        "pages_csv": pages_to_csv(records),
        "candidate_provisions_csv": provisions_to_csv(provisions),
        "manual_decisions_csv": decisions_to_csv(decisions),
        "ai_proposals_csv": ai_proposals_to_csv(proposal_records),
        "verification_results_csv": verification_results_to_csv(verifier_records),
    }
