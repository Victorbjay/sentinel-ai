import enum
from sqlalchemy import String, Text, Float, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.core.database import Base
from app.models.base import TimestampMixin


class ClaimStatus(str, enum.Enum):
    PENDING_HUMAN_REVIEW = "pending_human_review"
    UNDER_REVIEW = "under_review"
    VERIFIED_TRUE = "verified_true"
    DEBUNKED = "debunked"
    MISLEADING = "misleading"
    INCONCLUSIVE = "inconclusive"


class ClaimLanguage(str, enum.Enum):
    ENGLISH = "en"
    PIDGIN = "pcm"
    HAUSA = "ha"
    YORUBA = "yo"
    IGBO = "ig"
    OTHER = "other"


class Claim(Base, TimestampMixin):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_platform: Mapped[str] = mapped_column(String(64), default="web_news")
    author_anonymized_id: Mapped[str] = mapped_column(String(128), nullable=True)  # NDPA compliance: pseudonymized
    language: Mapped[ClaimLanguage] = mapped_column(
        Enum(ClaimLanguage, name="claim_language_enum"),
        default=ClaimLanguage.ENGLISH,
        nullable=False,
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="claim_status_enum"),
        default=ClaimStatus.PENDING_HUMAN_REVIEW,
        nullable=False,
        index=True,
    )
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    cluster_id: Mapped[Optional[int]] = mapped_column(ForeignKey("narratives.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    narrative: Mapped[Optional["NarrativeCluster"]] = relationship("NarrativeCluster", back_populates="claims")
    reviews: Mapped[List["HumanReviewAudit"]] = relationship("HumanReviewAudit", back_populates="claim", cascade="all, delete-orphan")
