from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.claim import Claim, ClaimStatus
from app.models.review import HumanReviewAudit
from app.schemas.review import HumanReviewCreate, HumanReviewRead

router = APIRouter()


@router.post("/", response_model=HumanReviewRead, status_code=201)
async def submit_human_review(payload: HumanReviewCreate, db: AsyncSession = Depends(get_db)):
    """
    Submits a human-in-the-loop adjudication on a flagged claim.
    Updates claim status, records immutable audit log, ensuring NDPA and Responsible AI compliance.
    """
    claim = await db.get(Claim, payload.claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Update claim status
    claim.status = payload.verdict

    # Record audit log
    audit = HumanReviewAudit(
        claim_id=payload.claim_id,
        reviewer_name=payload.reviewer_name,
        reviewer_role=payload.reviewer_role,
        verdict=payload.verdict.value if hasattr(payload.verdict, "value") else str(payload.verdict),
        rationale=payload.rationale,
        action_taken=payload.action_taken,
    )
    db.add(audit)
    await db.flush()
    await db.refresh(audit)
    return audit


@router.get("/claim/{claim_id}", response_model=List[HumanReviewRead])
async def get_reviews_for_claim(claim_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieves all human review audit records for a specific claim."""
    query = select(HumanReviewAudit).filter(HumanReviewAudit.claim_id == claim_id).order_by(HumanReviewAudit.created_at.desc())
    result = await db.scalars(query)
    return result.all()
