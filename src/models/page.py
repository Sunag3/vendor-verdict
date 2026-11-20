from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class VendorPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    case_id: str
    page_id: str

    url: str
    title: Optional[str] = None

    source_type: Optional[str] = None
    publisher: Optional[str] = None

    published_date: Optional[str] = None
    last_updated_date: Optional[str] = Field(None, alias="last_updated")

    text: Optional[str] = None