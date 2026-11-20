from typing import Any

from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    page_id: str
    chunk_id: str

    last_updated: str | None = None

    supporting_text: str = Field(
        description=(
            "Short factual excerpt or concise "
            "description of the evidence supporting "
            "the extracted fact."
        )

    )

class ExtractedFact(BaseModel):

    field_name: str = Field(
        description=(
            "Exact field requested by the requirement."
        )
    )

    missing: bool = Field(
        description=(
            "True when supplied evidence does not explicitly establish the requested fact."
        )
    )

    value: (
        str
        | int
        | float
        | bool
        | list[str]
        | None
    ) = Field(
        default=None,
        description="Normalized value for simple fields."
    )

    records: list[
        dict[str, Any]
    ] = Field(
        default_factory=list,
        description="Structured records for complex fields such as certificates, incidents or subprocessors."
    )

    evidence: list[
        EvidenceReference
    ] = Field(
        default_factory=list
    )

    notes: str | None = None