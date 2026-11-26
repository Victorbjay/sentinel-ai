import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.claim import Claim
from app.models.narrative import NarrativeCluster, ThreatLevel

# Cosine similarity threshold for joining an existing narrative cluster
SIMILARITY_THRESHOLD = 0.52
MAX_COSINE_DISTANCE = 1.0 - SIMILARITY_THRESHOLD


def _normalize_vector(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def _update_running_centroid(
    old_centroid: Optional[List[float]],
    new_embedding: List[float],
    old_count: int,
) -> List[float]:
    if not old_centroid or len(old_centroid) != len(new_embedding):
        return new_embedding
    total = old_count + 1
    updated = [
        (old_centroid[i] * old_count + new_embedding[i]) / total
        for i in range(len(new_embedding))
    ]
    return _normalize_vector(updated)


def _compute_threat_level(volume: int, risk_score: float) -> ThreatLevel:
    if volume >= 10 or (volume >= 4 and risk_score >= 0.8):
        return ThreatLevel.CRITICAL
    if volume >= 5 or risk_score >= 0.75:
        return ThreatLevel.HIGH
    if volume >= 2 or risk_score >= 0.5:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def _derive_cluster_title(cleaned_text: str) -> str:
    """Generates a concise cluster title from the founding claim."""
    words = cleaned_text.strip().split()
    snippet = " ".join(words[:10])
    if len(words) > 10:
        snippet += "..."
    return snippet or "Emerging Electoral Narrative"


async def assign_claim_to_narrative(
    db: AsyncSession,
    claim: Claim,
    claim_embedding: List[float],
) -> Tuple[NarrativeCluster, bool]:
    """
    Finds the nearest active NarrativeCluster in pgvector.
    If within SIMILARITY_THRESHOLD, attaches the claim and updates centroid/metrics.
    Otherwise creates a new NarrativeCluster.

    Returns (cluster, is_new_cluster).
    """
    distance_expr = NarrativeCluster.centroid_embedding.cosine_distance(claim_embedding)
    stmt = (
        select(NarrativeCluster, distance_expr.label("distance"))
        .where(
            NarrativeCluster.is_active.is_(True),
            NarrativeCluster.centroid_embedding.is_not(None),
        )
        .order_by(distance_expr)
        .limit(1)
    )
    row = (await db.execute(stmt)).first()

    if row is not None and row.distance is not None and row.distance <= MAX_COSINE_DISTANCE:
        cluster: NarrativeCluster = row[0]
        old_count = cluster.volume_count or 1
        cluster.centroid_embedding = _update_running_centroid(
            list(cluster.centroid_embedding),
            claim_embedding,
            old_count,
        )
        cluster.volume_count = old_count + 1

        # Calculate velocity (claims per hour since creation, minimum 1.0)
        created = cluster.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        hours_elapsed = max((datetime.now(timezone.utc) - created).total_seconds() / 3600.0, 0.25)
        cluster.velocity_score = round(cluster.volume_count / hours_elapsed, 2)

        # Escalate threat level if warranted (never downgrade automatically)
        candidate_threat = _compute_threat_level(cluster.volume_count, claim.risk_score)
        tier_order = {
            ThreatLevel.LOW: 0,
            ThreatLevel.MEDIUM: 1,
            ThreatLevel.HIGH: 2,
            ThreatLevel.CRITICAL: 3,
        }
        if tier_order[candidate_threat] > tier_order[cluster.threat_level]:
            cluster.threat_level = candidate_threat

        claim.cluster_id = cluster.id
        await db.flush()
        return cluster, False

    # Create new narrative cluster
    new_cluster = NarrativeCluster(
        title=_derive_cluster_title(claim.cleaned_text),
        description=f"Narrative cluster initialized from {claim.source_platform} ({claim.language.value}): {claim.cleaned_text}",
        threat_level=_compute_threat_level(1, claim.risk_score),
        volume_count=1,
        velocity_score=1.0,
        is_active=True,
        centroid_embedding=claim_embedding,
    )
    db.add(new_cluster)
    await db.flush()
    await db.refresh(new_cluster)

    claim.cluster_id = new_cluster.id
    await db.flush()
    return new_cluster, True
