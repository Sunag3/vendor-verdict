from typing import Literal

from pydantic import BaseModel, Field

from src.models.extracted_fact import EvidenceReference

Verdict = Literal[
    "PASS",
    "FAIL",
    "UNKNOWN",
    "NEEDS_REVIEW"
]


class RequirementVerdict(BaseModel):

    case_id: str
    requirement_id: str
    requirement_title: str

    field_name: str
    severity: str

    verdict: Verdict

    resolved_value: (
        str
        | int
        | float
        | bool
        | list[str]
        | None
    ) = None

    resolved_records: list[dict] = Field(default_factory=list)

    evidence: list[EvidenceReference] = Field(default_factory=list)

    reason: str

    resolution_status: str

    conflict: bool = False