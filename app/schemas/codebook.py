from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceRequirements(BaseModel):
    quotation_required: bool = True
    location_required: bool = True
    minimum_evidence_strength: float = Field(default=0.75, ge=0, le=1)


class CodebookVariableSchema(BaseModel):
    code: str
    family: str
    label: str
    description: str
    data_type: str
    allowed_values: list[Any]
    risk_level: str = "medium"
    mandatory_human_review: bool = False
    dependencies: dict[str, Any] = Field(default_factory=dict)
    positive_criteria: list[str] = Field(default_factory=list)
    negative_criteria: list[str] = Field(default_factory=list)
    positive_examples: list[dict[str, str]] = Field(default_factory=list)
    negative_examples: list[dict[str, str]] = Field(default_factory=list)
    evidence_requirements: EvidenceRequirements = Field(default_factory=EvidenceRequirements)


class CodebookSchema(BaseModel):
    version: str
    title: str
    variables: list[CodebookVariableSchema]

