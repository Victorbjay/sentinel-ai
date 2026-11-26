from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.services.nlp.multilingual import process_claim_text, compute_claim_risk_score
from app.services.embeddings import generate_embedding
from app.services.clustering import assign_claim_to_narrative
from app.services.rag import search_relevant_facts

router = APIRouter()

SYNTHETIC_ELECTION_FEED: List[Dict[str, str]] = [
    {
        "raw_text": "Dem say BVAS don spoil for PU 014 Eti-Osa, make una go house no voting today!",
        "source_platform": "whatsapp_forward",
        "author_anonymized_id": "sim_anon_001",
    },
    {
        "raw_text": "BREAKING: IReV server has been hacked so manual Form EC8A results at polling units are cancelled.",
        "source_platform": "x_twitter",
        "author_anonymized_id": "sim_anon_002",
    },
    {
        "raw_text": "Jami'an zabe sun rufe akwati tun karfe 2:30 na rana duk da mutane suna kan layi.",
        "source_platform": "facebook_public",
        "author_anonymized_id": "sim_anon_003",
    },
    {
        "raw_text": "You can now print your PVC online or send your brother to collect it at the ward center.",
        "source_platform": "telegram_channel",
        "author_anonymized_id": "sim_anon_004",
    },
    {
        "raw_text": "Awon oludije ti kede ara won gege bi olubori ibo ki INEC to pari kika.",
        "source_platform": "x_twitter",
        "author_anonymized_id": "sim_anon_005",
    },
    {
        "raw_text": "Unofficial social media blog just declared a presidential winner before INEC collation!",
        "source_platform": "web_blog",
        "author_anonymized_id": "sim_anon_006",
    },
]


@router.post("/run")
async def run_election_day_simulation(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Injects a synthetic, NDPA-compliant multilingual batch of election-day claims
    (Pidgin, English, Hausa, Yoruba) to demonstrate real-time clustering and RAG matching.
    """
    ingested = []
    for item in SYNTHETIC_ELECTION_FEED:
        cleaned, lang = process_claim_text(item["raw_text"])
        risk = compute_claim_risk_score(item["raw_text"], cleaned)
        embedding = generate_embedding(cleaned)

        claim = Claim(
            raw_text=item["raw_text"],
            cleaned_text=cleaned,
            source_platform=item["source_platform"],
            author_anonymized_id=item["author_anonymized_id"],
            language=lang,
            status=ClaimStatus.PENDING_HUMAN_REVIEW,
            risk_score=risk,
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

    return {
        "simulated_count": len(ingested),
        "message": "Synthetic multilingual election-day feed processed and queued for human review.",
        "items": ingested,
    }
