from __future__ import annotations

from typing import Any

from app.schemas.codebook import CodebookVariableSchema


def normalise_value(value: Any) -> str:
    return str(value).strip()


def latest_decisions_by_variable(
    decisions: list[dict[str, Any]],
    provision_id: str,
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for decision in sorted(decisions, key=lambda item: item.get("created_at", "")):
        if decision.get("provision_id") == provision_id:
            latest[decision["variable_code"]] = decision
    return latest


def evaluate_dependency_rules(
    variable: CodebookVariableSchema,
    proposed_value: Any,
    existing_decisions: list[dict[str, Any]],
    provision_id: str,
) -> dict[str, Any]:
    dependencies = variable.dependencies or {}
    required = dependencies.get("requires", {})
    if normalise_value(proposed_value) in {"0", "False", "false", "None", ""}:
        return {
            "status": "not_applicable",
            "violations": [],
            "requirements": required,
        }

    latest = latest_decisions_by_variable(existing_decisions, provision_id)
    violations = []
    for required_code, required_value in required.items():
        decision = latest.get(required_code)
        if decision is None:
            violations.append(
                {
                    "required_variable": required_code,
                    "required_value": normalise_value(required_value),
                    "actual_value": None,
                    "reason": "missing_required_decision",
                }
            )
            continue
        actual_value = normalise_value(decision.get("proposed_value"))
        if actual_value != normalise_value(required_value):
            violations.append(
                {
                    "required_variable": required_code,
                    "required_value": normalise_value(required_value),
                    "actual_value": actual_value,
                    "reason": "required_value_not_met",
                }
            )

    return {
        "status": "pass" if not violations else "violation",
        "violations": violations,
        "requirements": required,
    }


def summarize_rule_result(result: dict[str, Any]) -> str:
    if result["status"] == "not_applicable":
        return "No dependency check is required for this value."
    if result["status"] == "pass":
        return "Dependency checks passed."
    pieces = [
        f"{violation['required_variable']} must be {violation['required_value']}"
        for violation in result["violations"]
    ]
    return "Rule conflict: " + "; ".join(pieces)

