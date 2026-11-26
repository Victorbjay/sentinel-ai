from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.narrative import NarrativeCluster
from app.schemas.narrative import NarrativeCreate, NarrativeRead

router = APIRouter()


@router.post("/", response_model=NarrativeRead, status_code=201)
async def create_narrative(payload: NarrativeCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new narrative cluster."""
    cluster = NarrativeCluster(
        title=payload.title,
        description=payload.description,
        threat_level=payload.threat_level,
    )
    db.add(cluster)
    await db.flush()
    await db.refresh(cluster)
    return cluster


@router.get("/", response_model=List[NarrativeRead])
async def list_narratives(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves active narrative clusters ordered by volume and velocity."""
    query = select(NarrativeCluster).order_by(
        NarrativeCluster.volume_count.desc(),
        NarrativeCluster.velocity_score.desc(),
    ).limit(limit)

    result = await db.scalars(query)
    return result.all()
