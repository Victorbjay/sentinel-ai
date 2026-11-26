import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.verified_fact import VerifiedFact
from app.services.embeddings import generate_embedding


async def search_relevant_facts(
    db: AsyncSession,
    query_text: str,
    top_k: int = 3,
    topic_filter: Optional[str] = None,
    query_embedding: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Searches verified electoral facts using pgvector cosine distance on semantic embeddings,
    returning ranked matches with similarity_score (0.0 to 1.0).
    Falls back to keyword matching if vector search is unavailable.
    """
    query_vec = query_embedding or generate_embedding(query_text)

    results: List[Dict[str, Any]] = []
    try:
        distance_expr = VerifiedFact.embedding.cosine_distance(query_vec)
        query = select(VerifiedFact, distance_expr.label("distance")).where(
            VerifiedFact.embedding.is_not(None)
        )
        if topic_filter:
            query = query.where(VerifiedFact.topic.ilike(f"%{topic_filter}%"))

        query = query.order_by(distance_expr).limit(top_k)
        rows = (await db.execute(query)).all()

        for fact, distance in rows:
            similarity = round(max(0.0, 1.0 - float(distance)), 4) if distance is not None else 0.0
            results.append({
                "id": fact.id,
                "topic": fact.topic,
                "claim_summary": fact.claim_summary,
                "official_fact": fact.official_fact,
                "official_source": fact.official_source,
                "source_url": fact.source_url,
                "similarity_score": similarity,
            })
    except Exception:
        search_words = [w for w in re.findall(r"\w+", query_text.lower()) if len(w) > 3][:3]
        if search_words:
            conditions = [
                or_(
                    VerifiedFact.claim_summary.ilike(f"%{w}%"),
                    VerifiedFact.official_fact.ilike(f"%{w}%"),
                )
                for w in search_words
            ]
            fallback_query = select(VerifiedFact).where(or_(*conditions)).limit(top_k)
            fallback_facts = (await db.scalars(fallback_query)).all()
            for fact in fallback_facts:
                results.append({
                    "id": fact.id,
                    "topic": fact.topic,
                    "claim_summary": fact.claim_summary,
                    "official_fact": fact.official_fact,
                    "official_source": fact.official_source,
                    "source_url": fact.source_url,
                    "similarity_score": None,
                })

    return results
