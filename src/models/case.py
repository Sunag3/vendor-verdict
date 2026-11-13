from typing import Optional
from pydantic import BaseModel, Field

from src.models.page import VendorPage

class VendorCase(BaseModel):
    case_id: str
    split: str

    vendor: str
    legal_entity: str
    official_domain: str

    hq_country: Optional[str] = None
    hq_city: Optional[str] = None

    product: Optional[str] = None
    question: Optional[str] = None

    tier: Optional[str] = None
    users: Optional[int] = None

    as_of: Optional[str] = None
    pages: Optional[list[VendorPage]] = Field(
        default_factory=list
    )