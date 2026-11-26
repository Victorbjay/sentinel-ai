from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class VerifiedFactBase(BaseModel):
    topic: str
    claim_summary: str
    official_fact: str
    official_source: str
    source_url: Optional[str] = None


class VerifiedFactCreate(VerifiedFactBase):
    embedding: Optional[List[float]] = None


class VerifiedFactRead(VerifiedFactBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FactSearchQuery(BaseModel):
    query_text: str
    top_k: int = 3
    topic_filter: Optional[str] = None
