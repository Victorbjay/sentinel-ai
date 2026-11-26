import enum
from sqlalchemy import String, Text, Float, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import VECTOR
from typing import List, Optional
from app.core.config import settings
from app.core.database import Base
from app.models.base import TimestampMixin


class ThreatLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NarrativeCluster(Base, TimestampMixin):
    __tablename__ = "narratives"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    threat_level: Mapped[ThreatLevel] = mapped_column(
        Enum(ThreatLevel, name="threat_level_enum"),
        default=ThreatLevel.LOW,
        nullable=False,
    )
    volume_count: Mapped[int] = mapped_column(Integer, default=1)
    velocity_score: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(default=True)
    centroid_embedding: Mapped[Optional[List[float]]] = mapped_column(
        VECTOR(settings.EMBEDDING_DIMENSION), nullable=True
    )

    # Relationships
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="narrative")
