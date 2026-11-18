from typing import Any

from pydantic import BaseModel

class RetrievedEvidence(BaseModel):
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float