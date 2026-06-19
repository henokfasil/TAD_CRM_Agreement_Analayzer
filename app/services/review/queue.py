from __future__ import annotations

from typing import Any


def build_uncoded_provision_queue(
    provisions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coded_provision_ids = {decision["provision_id"] for decision in decisions}
    return [provision for provision in provisions if provision["provision_id"] not in coded_provision_ids]


def build_decision_review_queue(
    decisions: list[dict[str, Any]],
    statuses: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected_statuses = statuses or {"provisional", "uncertain"}
    return [decision for decision in decisions if decision["reviewer_status"] in selected_statuses]

