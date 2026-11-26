from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any, Literal
from app.core.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.models.narrative import NarrativeCluster, ThreatLevel
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimWithVerification
from app.services.nlp.multilingual import (
    process_claim_text,
    compute_claim_risk_score,
    compute_triage_priority,
    pseudonymize_author,
)
from app.services.embeddings import generate_embedding
from app.services.clustering import assign_claim_to_narrative
from app.services.rag import search_relevant_facts
from app.services.explainer import generate_explainability_brief
from app.services.media_screening import screen_media_artifact

router = APIRouter()


@router.get("/stats")
async def get_monitoring_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Returns exact database counts for dashboard KPIs (no pagination cap)."""
    total_claims = (await db.scalar(select(func.count(Claim.id)))) or 0
    pending_review = (
        await db.scalar(
            select(func.count(Claim.id)).where(Claim.status == ClaimStatus.PENDING_HUMAN_REVIEW)
        )
    ) or 0
    total_clusters = (await db.scalar(select(func.count(NarrativeCluster.id)))) or 0
    urgent_threats = (
        await db.scalar(
            select(func.count(NarrativeCluster.id)).where(
                NarrativeCluster.threat_level.in_([ThreatLevel.HIGH, ThreatLevel.CRITICAL])
            )
        )
    ) or 0

    return {
        "total_claims": total_claims,
        "pending_human_review": pending_review,
        "total_clusters": total_clusters,
        "urgent_threats": urgent_threats,
    }


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
    priority = compute_triage_priority(risk, payload.spread_score, payload.synthetic_media_attached)
    embedding = generate_embedding(cleaned)
    safe_author = pseudonymize_author(payload.author_anonymized_id)

    claim = Claim(
        raw_text=payload.raw_text,
        cleaned_text=cleaned,
        source_platform=payload.source_platform or "web_news",
        author_anonymized_id=safe_author,
        language=lang,
        status=ClaimStatus.PENDING_HUMAN_REVIEW,
        risk_score=risk,
        spread_score=payload.spread_score,
        synthetic_media_attached=payload.synthetic_media_attached,
        triage_priority=priority,
        embedding=embedding,
    )
    db.add(claim)
    await db.flush()
    await db.refresh(claim)

    cluster, is_new_cluster = await assign_claim_to_narrative(db, claim, embedding)
    await db.refresh(claim)

    matched_facts = await search_relevant_facts(
        db, cleaned, top_k=2, query_embedding=embedding
    )
    explanation = await generate_explainability_brief(
        cleaned_text=cleaned,
        language=lang,
        risk_score=risk,
        matched_facts=matched_facts,
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
        spread_score=claim.spread_score,
        synthetic_media_attached=claim.synthetic_media_attached,
        triage_priority=claim.triage_priority,
        cluster_id=claim.cluster_id,
        narrative_title=cluster.title,
        is_new_cluster=is_new_cluster,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        matched_facts=matched_facts,
        explanation=explanation,
        recommended_action=(
            "Cross-referenced with INEC guidelines. Flagged for accredited fact-checker review."
            if matched_facts else
            "Pending verification: no direct contradictory rule found. Requires observer verification."
        ),
    )


@router.post("/screen-media")
async def screen_uploaded_media(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Track 1D Synthetic Media Screening Assistant:
    Inspects uploaded election image/flyer metadata and guides human verification steps.
    """
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit.")
    return await screen_media_artifact(
        image_bytes=contents,
        filename=file.filename or "upload.jpg",
        mime_type=file.content_type or "image/jpeg",
    )


@router.get("/", response_model=List[ClaimRead])
async def list_claims(
    status: Optional[ClaimStatus] = Query(None, description="Filter by claim status"),
    cluster_id: Optional[int] = Query(None, description="Filter by narrative cluster ID"),
    sort_by: Literal["priority", "recent"] = Query("priority", description="Triage sort order"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Lists ingested claims ranked by triage priority (default) or recency."""
    order_cols = (
        [Claim.triage_priority.desc(), Claim.created_at.desc()]
        if sort_by == "priority"
        else [Claim.created_at.desc()]
    )
    query = select(Claim).order_by(*order_cols).offset(offset).limit(limit)
    if status:
        query = query.where(Claim.status == status)
    if cluster_id is not None:
        query = query.where(Claim.cluster_id == cluster_id)

    result = await db.scalars(query)
    return result.all()


@router.get("/{claim_id}", response_model=ClaimWithVerification)
async def get_claim_detail(claim_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieves a single claim with cross-referenced verified facts and explainability."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    narrative_title = None
    if claim.cluster_id:
        cluster = await db.get(NarrativeCluster, claim.cluster_id)
        if cluster:
            narrative_title = cluster.title

    stored_embedding = list(claim.embedding) if claim.embedding is not None else None
    matched_facts = await search_relevant_facts(
        db, claim.cleaned_text, top_k=3, query_embedding=stored_embedding
    )
    explanation = await generate_explainability_brief(
        cleaned_text=claim.cleaned_text,
        language=claim.language,
        risk_score=claim.risk_score,
        matched_facts=matched_facts,
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
        spread_score=claim.spread_score,
        synthetic_media_attached=claim.synthetic_media_attached,
        triage_priority=claim.triage_priority,
        cluster_id=claim.cluster_id,
        narrative_title=narrative_title,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
        matched_facts=matched_facts,
        explanation=explanation,
        recommended_action="Requires human verification prior to public dissemination.",
    )
