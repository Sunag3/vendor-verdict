from typing import Any, Literal

from pydantic import BaseModel, Field

from src.models.extracted_fact import EvidenceReference


class ResolvedFact(BaseModel):

    field_name: str

    missing: bool

    value: (
        str
        | int
        | float
        | bool
        | list[str]
        | None
    ) = None

    records: list[dict[str, Any]] = Field(default_factory=list)

    evidence: list[EvidenceReference] = Field(default_factory=list)

    conflict: bool = False

    resolution_status: Literal["resolved", "missing", "unresolved_conflict"]

    ignored_future_candidates: int = 0

    notes: str | None = None