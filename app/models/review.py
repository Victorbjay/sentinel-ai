from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.claim import ClaimStatus


class HumanReviewAudit(Base, TimestampMixin):
    """
    Immutable audit trail for Human-in-the-Loop review actions.
    Ensures accountability and strict ethical AI oversight.
    """
    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(128), default="Election Observer / Fact-Checker")
    verdict: Mapped[str] = mapped_column(String(64), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str] = mapped_column(String(128), default="reviewed_and_categorized")

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="reviews")
