from typing import Optional
from pydantic import BaseModel


class EvidenceChunk(BaseModel):
    chunk_id: str
    case_id: str
    page_id: str

    chunk_index: int
    total_chunks: int

    text: str
    word_count: int

    start_word: int
    end_word: int

    content_hash: str

    url: str

    # optional fields
    title: Optional[str] = None
    source_type: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    last_updated: Optional[str] = None
    source_category: str

    official_domain_match: bool
    legal_entity_match: bool
    certificate_registry_match: bool

    trusted_source: bool
    usabled_evidence: bool

    trust_level: str

    injection_flag: bool