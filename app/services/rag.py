import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.verified_fact import VerifiedFact
from app.core.config import settings


def generate_mock_or_deterministic_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Generates a normalized deterministic pseudo-embedding vector for environments
    running in lightweight mode (e.g. without downloading 500MB HuggingFace models),
    while preserving deterministic vector similarity on token overlap.
    In full production, this can be swapped with sentence-transformers.
    """
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    for word in words:
        # Hash token into dimension buckets
        h = hash(word)
        idx1 = abs(h) % dim
        idx2 = abs(h * 31) % dim
        vec[idx1] += 1.0
        vec[idx2] += 0.5

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


async def search_relevant_facts(
    db: AsyncSession,
    query_text: str,
    top_k: int = 3,
    topic_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches verified facts using pgvector cosine distance,
    falling back to keyword matching when vector index is unpopulated.
    """
    query_vec = generate_mock_or_deterministic_embedding(query_text, settings.EMBEDDING_DIMENSION)

    results = []
    try:
        # Attempt pgvector cosine similarity search
        query = select(VerifiedFact)
        if topic_filter:
            query = query.filter(VerifiedFact.topic.ilike(f"%{topic_filter}%"))

        # Order by cosine distance ascending
        query = query.order_by(VerifiedFact.embedding.cosine_distance(query_vec)).limit(top_k)
        executed = await db.scalars(query)
        facts = executed.all()

        for f in facts:
            results.append({
                "id": f.id,
                "topic": f.topic,
                "claim_summary": f.claim_summary,
                "official_fact": f.official_fact,
                "official_source": f.official_source,
                "source_url": f.source_url,
            })
    except Exception:
        # Fallback to ILIKE text matching
        search_words = [w for w in re.findall(r"\w+", query_text.lower()) if len(w) > 3][:3]
        if search_words:
            conditions = [
                or_(
                    VerifiedFact.claim_summary.ilike(f"%{w}%"),
                    VerifiedFact.official_fact.ilike(f"%{w}%")
                )
                for w in search_words
            ]
            fallback_query = select(VerifiedFact).filter(or_(*conditions)).limit(top_k)
            fallback_exec = await db.scalars(fallback_query)
            fallback_facts = fallback_exec.all()
            for f in fallback_facts:
                results.append({
                    "id": f.id,
                    "topic": f.topic,
                    "claim_summary": f.claim_summary,
                    "official_fact": f.official_fact,
                    "official_source": f.official_source,
                    "source_url": f.source_url,
                })

    return results
