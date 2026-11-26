from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.verified_fact import VerifiedFact
from app.schemas.verified_fact import VerifiedFactCreate, VerifiedFactRead, FactSearchQuery
from app.services.embeddings import generate_embedding
from app.services.rag import search_relevant_facts

router = APIRouter()


@router.post("/", response_model=VerifiedFactRead, status_code=201)
async def create_verified_fact(payload: VerifiedFactCreate, db: AsyncSession = Depends(get_db)):
    """Creates an authoritative verified electoral fact with generated semantic embedding."""
    embedding = payload.embedding
    if not embedding:
        embedding = generate_embedding(
            f"{payload.topic} {payload.claim_summary} {payload.official_fact}"
        )

    fact = VerifiedFact(
        topic=payload.topic,
        claim_summary=payload.claim_summary,
        official_fact=payload.official_fact,
        official_source=payload.official_source,
        source_url=payload.source_url,
        embedding=embedding,
    )
    db.add(fact)
    await db.flush()
    await db.refresh(fact)
    return fact


@router.get("/", response_model=List[VerifiedFactRead])
async def list_verified_facts(
    topic: str = Query(None, description="Filter by topic"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Lists verified electoral facts in the knowledge base."""
    query = select(VerifiedFact).order_by(VerifiedFact.id.desc()).limit(limit)
    if topic:
        query = query.filter(VerifiedFact.topic.ilike(f"%{topic}%"))
    result = await db.scalars(query)
    return result.all()


@router.post("/search")
async def search_facts(payload: FactSearchQuery, db: AsyncSession = Depends(get_db)):
    """Executes pgvector similarity search against verified electoral facts."""
    matches = await search_relevant_facts(
        db,
        query_text=payload.query_text,
        top_k=payload.top_k,
        topic_filter=payload.topic_filter,
    )
    return {"query": payload.query_text, "results": matches}
