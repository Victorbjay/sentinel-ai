from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.narrative import ThreatLevel
from app.schemas.claim import ClaimRead


class NarrativeBase(BaseModel):
    title: str
    description: str
    threat_level: ThreatLevel = ThreatLevel.LOW


class NarrativeCreate(NarrativeBase):
    pass


class NarrativeRead(NarrativeBase):
    id: int
    volume_count: int
    velocity_score: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NarrativeDetail(NarrativeRead):
    claims: List[ClaimRead] = []
