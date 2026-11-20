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


class FactCandidate(BaseModel):
    """
    One factual value extracted from one source/chunk.

    Simple fields:
        value is poulated.
    
    Complex fields:
        record is populated.
    """

    page_id: str
    chunk_id: str

    last_updated: str | None = None

    value: (
        str
        | int
        | float
        | bool
        | list[str]
        | None
    ) = None

    record: dict[str, Any] | None = None


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


    # STEP 7 add candidates

    candidates: list[
        FactCandidate
    ] = Field(
        default_factory=list,
        description="List of candidate facts extracted from various sources/chunks."
    )

    notes: str | None = None


