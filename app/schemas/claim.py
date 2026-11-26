from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.claim import ClaimStatus, ClaimLanguage


class ClaimBase(BaseModel):
    raw_text: str
    source_platform: Optional[str] = "web_news"
    author_anonymized_id: Optional[str] = None


class ClaimCreate(ClaimBase):
    pass


class ClaimRead(ClaimBase):
    id: int
    cleaned_text: str
    language: ClaimLanguage
    status: ClaimStatus
    risk_score: float
    cluster_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimWithVerification(ClaimRead):
    narrative_title: Optional[str] = None
    is_new_cluster: Optional[bool] = None
    matched_facts: List[dict] = []
    explanation: Optional[Dict[str, Any]] = None
    recommended_action: str = "Awaiting verification from accredited observers."
