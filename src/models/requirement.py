from typing import Optional, Any
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    id: str
    title: Optional[str] = None

    raw: dict[str, Any] = Field(
        default_factory=dict
    )