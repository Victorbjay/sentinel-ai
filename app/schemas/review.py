from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.claim import ClaimStatus


class HumanReviewCreate(BaseModel):
    claim_id: int
    reviewer_name: str
    reviewer_role: str = "Accredited Fact-Checker"
    verdict: ClaimStatus
    rationale: str
    action_taken: str = "reviewed_and_adjudicated"


class HumanReviewRead(BaseModel):
    id: int
    claim_id: int
    reviewer_name: str
    reviewer_role: str
    verdict: str
    rationale: str
    action_taken: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
