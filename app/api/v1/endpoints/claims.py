from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimWithVerification
from app.services.nlp.multilingual import process_claim_text, compute_claim_risk_score
from app.services.embeddings import generate_embedding
from app.services.clustering import assign_claim_to_narrative
from app.services.rag import search_relevant_facts

router = APIRouter()


@router.post("/", response_model=ClaimWithVerification, status_code=201)
async def ingest_claim(payload: ClaimCreate, db: AsyncSession = Depends(get_db)):
    """
    Ingests an election-related claim or social signal, cleans and normalizes it,
    detects regional language (English, Pidgin, Hausa, Yoruba, Igbo),
    assigns it to a semantic narrative cluster in pgvector,
    and cross-references against verified INEC facts via vector RAG.
    """
    cleaned, lang = process_claim_text(payload.raw_text)
    risk = compute_claim_risk_score(payload.raw_text, cleaned)
    embedding = generate_embedding(cleaned)

    claim = Claim(
        raw_text=payload.raw_text,
        cleaned_text=cleaned,
        source_platform=payload.source_platform or "web_news",
        author_anonymized_id=payload.author_anonymized_id,
        language=lang,
        status=ClaimStatus.PENDING_HUMAN_REVIEW,
        risk_score=risk,
        embedding=embedding,
    )
    db.add(claim)
    await db.flush()
    await db.refresh(claim)

    # Assign to semantic narrative cluster
    cluster, is_new_cluster = await assign_claim_to_narrative(db, claim, embedding)
    await db.refresh(claim)

    # Search verified INEC facts for rationale
    matched_facts = await search_relevant_facts(
        db, cleaned, top_k=2, query_embedding=embedding
    )

    return ClaimWithVerification(
        id=claim.id,
        raw_text=claim.raw_text,
        cleaned_text=claim.cleaned_text,
        source_platform=claim.source_platform,
        author_anonymized_id=claim.author_anonymized_id,
        language=claim.language,
        status=claim.status,
        risk_score=claim.risk_score,
        cluster_id=claim.cluster_id,
        narrative_title=cluster.title,
        is_new_cluster=is_new_cluster,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        matched_facts=matched_facts,
        recommended_action=(
            "Cross-referenced with INEC guidelines. Flagged for accredited fact-checker review."
            if matched_facts else
            "Pending verification: no direct contradictory rule found. Requires observer verification."
        ),
    )


@router.get("/", response_model=List[ClaimRead])
async def list_claims(
    status: Optional[ClaimStatus] = Query(None, description="Filter by claim status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Lists ingested claims with pagination and status filters."""
    query = select(Claim).order_by(Claim.created_at.desc()).offset(offset).limit(limit)
    if status:
        query = query.filter(Claim.status == status)

    result = await db.scalars(query)
    return result.all()


@router.get("/{claim_id}", response_model=ClaimWithVerification)
async def get_claim_detail(claim_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieves a single claim with cross-referenced verified facts."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    matched_facts = await search_relevant_facts(db, claim.cleaned_text, top_k=3)

    return ClaimWithVerification(
        id=claim.id,
        raw_text=claim.raw_text,
        cleaned_text=claim.cleaned_text,
        source_platform=claim.source_platform,
        author_anonymized_id=claim.author_anonymized_id,
        language=claim.language,
        status=claim.status,
        risk_score=claim.risk_score,
        cluster_id=claim.cluster_id,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        matched_facts=matched_facts,
        recommended_action="Requires human verification prior to public dissemination.",
    )
