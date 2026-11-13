from typing import Optional
from pydantic import BaseModel
from src.models.page import VendorPage


class SourceValidationResult(BaseModel):
    page_id: str
    case_id: str
    source_category: str

    # Boolean fields
    official_domain_match: bool = False
    legal_entity_match: bool = False
    certificate_registry_match: bool = False

    trusted_source: bool = False
    usable_evidence: bool = False

    injection_flag: bool = False
    trust_level: str = "untrusted"
    rejection_reason: Optional[str] = None


class ValidatedEvidencePage(BaseModel):
    page: VendorPage
    validation: SourceValidationResult