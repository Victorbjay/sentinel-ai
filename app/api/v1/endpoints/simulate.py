from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.models.narrative import NarrativeCluster
from app.services.nlp.multilingual import (
    process_claim_text,
    compute_claim_risk_score,
    compute_triage_priority,
)
from app.services.embeddings import generate_embedding
from app.services.clustering import assign_claim_to_narrative
from app.services.rag import search_relevant_facts

router = APIRouter()

SYNTHETIC_ELECTION_FEED: List[Dict[str, Any]] = [
    {
        "raw_text": "Dem say BVAS don spoil for PU 014 Eti-Osa, make una go house no voting today!",
        "source_platform": "whatsapp_forward",
        "author_anonymized_id": "sim_anon_001",
        "spread_score": 88,
        "synthetic_media_attached": False,
    },
    {
        "raw_text": "BREAKING: IReV server has been hacked so manual Form EC8A results at polling units are cancelled.",
        "source_platform": "x_twitter",
        "author_anonymized_id": "sim_anon_002",
        "spread_score": 93,
        "synthetic_media_attached": True,
    },
    {
        "raw_text": "Jami'an zabe sun rufe akwati tun karfe 2:30 na rana duk da mutane suna kan layi.",
        "source_platform": "facebook_public",
        "author_anonymized_id": "sim_anon_003",
        "spread_score": 74,
        "synthetic_media_attached": False,
    },
    {
        "raw_text": "You can now print your PVC online or send your brother to collect it at the ward center.",
        "source_platform": "telegram_channel",
        "author_anonymized_id": "sim_anon_004",
        "spread_score": 65,
        "synthetic_media_attached": False,
    },
    {
        "raw_text": "Awon oludije ti kede ara won gege bi olubori ibo ki INEC to pari kika.",
        "source_platform": "x_twitter",
        "author_anonymized_id": "sim_anon_005",
        "spread_score": 81,
        "synthetic_media_attached": False,
    },
    {
        "raw_text": "Ndi omempako kwuputa na ha meriri ntuli aka tupu INEC agucha vootu.",
        "source_platform": "whatsapp_forward",
        "author_anonymized_id": "sim_anon_006",
        "spread_score": 79,
        "synthetic_media_attached": False,
    },
    {
        "raw_text": "Unofficial social media blog just declared a presidential winner before INEC collation!",
        "source_platform": "web_news",
        "author_anonymized_id": "sim_anon_007",
        "spread_score": 91,
        "synthetic_media_attached": True,
    },
]


@router.post("/run")
async def run_election_day_simulation(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Injects a synthetic, NDPA-compliant multilingual batch of election-day claims
    (Pidgin, English, Hausa, Yoruba, Igbo). Idempotent: skips if already loaded.
    """
    existing_ids = set(
        (
            await db.scalars(
                select(Claim.author_anonymized_id).where(
                    Claim.author_anonymized_id.like("sim_anon_%")
                )
            )
        ).all()
    )

    ingested = []
    for item in SYNTHETIC_ELECTION_FEED:
        if item["author_anonymized_id"] in existing_ids:
            continue

        cleaned, lang = process_claim_text(item["raw_text"])
        risk = compute_claim_risk_score(item["raw_text"], cleaned)
        spread = int(item.get("spread_score", 50))
        has_media = bool(item.get("synthetic_media_attached", False))
        priority = compute_triage_priority(risk, spread, has_media)
        embedding = generate_embedding(cleaned)

        claim = Claim(
            raw_text=item["raw_text"],
            cleaned_text=cleaned,
            source_platform=item["source_platform"],
            author_anonymized_id=item["author_anonymized_id"],
            language=lang,
            status=ClaimStatus.PENDING_HUMAN_REVIEW,
            risk_score=risk,
            spread_score=spread,
            synthetic_media_attached=has_media,
            triage_priority=priority,
            embedding=embedding,
        )
        db.add(claim)
        await db.flush()
        await db.refresh(claim)

        cluster, is_new = await assign_claim_to_narrative(db, claim, embedding)
        facts = await search_relevant_facts(db, cleaned, top_k=1, query_embedding=embedding)

        ingested.append({
            "claim_id": claim.id,
            "language": claim.language.value,
            "risk_score": claim.risk_score,
            "cluster_id": cluster.id,
            "narrative_title": cluster.title,
            "is_new_cluster": is_new,
            "top_matched_fact": facts[0]["topic"] if facts else None,
        })

    if not ingested:
        return {
            "simulated_count": 0,
            "already_seeded": True,
            "message": "Sample election rumors are already loaded. Click 'Reset Demo' to clear and re-run.",
            "items": [],
        }

    return {
        "simulated_count": len(ingested),
        "already_seeded": False,
        "message": "Synthetic multilingual election-day feed processed and queued for human review.",
        "items": ingested,
    }


@router.post("/reset")
async def reset_demo_data(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Clears all synthetic demo claims and empty narrative clusters so testers/judges
    can run a clean demonstration from scratch (preserves verified INEC facts).
    """
    deleted_claims = await db.execute(delete(Claim))
    deleted_clusters = await db.execute(delete(NarrativeCluster))
    await db.flush()

    return {
        "status": "reset_complete",
        "deleted_claims": deleted_claims.rowcount or 0,
        "deleted_clusters": deleted_clusters.rowcount or 0,
        "message": "Demo claims and narrative clusters cleared. Verified INEC facts preserved.",
    }
