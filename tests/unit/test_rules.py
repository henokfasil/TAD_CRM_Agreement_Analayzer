from app.schemas.codebook import CodebookVariableSchema
from app.services.classification.rules import evaluate_dependency_rules, summarize_rule_result


def test_dependency_rule_detects_missing_required_decision() -> None:
    variable = CodebookVariableSchema(
        code="inv_spec_def",
        family="investment",
        label="Specific investment",
        description="test",
        data_type="binary",
        allowed_values=[0, 1],
        dependencies={"requires": {"inv_gen_ref": 1}},
    )

    result = evaluate_dependency_rules(variable, "1", [], "prov1")

    assert result["status"] == "violation"
    assert result["violations"][0]["reason"] == "missing_required_decision"
    assert "inv_gen_ref" in summarize_rule_result(result)


def test_dependency_rule_passes_when_requirement_met() -> None:
    variable = CodebookVariableSchema(
        code="inv_crm",
        family="investment",
        label="CRM investment",
        description="test",
        data_type="binary",
        allowed_values=[0, 1],
        dependencies={"requires": {"inv_gen_ref": 1}},
    )
    decisions = [
        {
            "provision_id": "prov1",
            "variable_code": "inv_gen_ref",
            "proposed_value": "1",
            "created_at": "2026-06-19T00:00:00+00:00",
        }
    ]

    result = evaluate_dependency_rules(variable, "1", decisions, "prov1")

    assert result["status"] == "pass"


def test_dependency_rule_not_applicable_for_negative_value() -> None:
    variable = CodebookVariableSchema(
        code="inv_crm",
        family="investment",
        label="CRM investment",
        description="test",
        data_type="binary",
        allowed_values=[0, 1],
        dependencies={"requires": {"inv_gen_ref": 1}},
    )

    result = evaluate_dependency_rules(variable, "0", [], "prov1")

    assert result["status"] == "not_applicable"
