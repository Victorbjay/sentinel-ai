from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import VECTOR
from typing import List, Optional
from app.core.database import Base
from app.models.base import TimestampMixin
from app.core.config import settings


class VerifiedFact(Base, TimestampMixin):
    """
    Authoritative repository of verified electoral rules, INEC guidelines,
    and official statements used for Vector RAG cross-referencing.
    """
    __tablename__ = "verified_facts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String(128), index=True, nullable=False)  # e.g., 'BVAS', 'Collation', 'PVC'
    claim_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    official_fact: Mapped[str] = mapped_column(Text, nullable=False)
    official_source: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "INEC Electoral Act 2022 Sec. 60"
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # 384-dimensional dense vector for semantic similarity lookup
    embedding: Mapped[List[float]] = mapped_column(VECTOR(settings.EMBEDDING_DIMENSION), nullable=True)
