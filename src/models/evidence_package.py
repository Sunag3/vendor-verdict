from typing import Any

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    chunk_id: str
    page_id: str

    text: str
    distance: float

    metadata: dict[str, Any]


class EvidencePackage(BaseModel):
    case_id: str
    requirement_id: str
    requirement_title: str
    field_name: str
    rule_name: str
    rule_params: dict[str, Any]
    severity: str
    query: str
    chunks: list[RetrievedChunk]
    page_ids: list[str]
    evidence_count: int