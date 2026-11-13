from typing import Optional

from pydantic import BaseModel

class VendorPage(BaseModel):
    case_id: str
    page_id: str

    url: str
    title: Optional[str] = None

    source_type: Optional[str] = None
    publisher: Optional[str] = None

    published_date: Optional[str] = None
    last_updated_date: Optional[str] = None

    text: Optional[str] = None