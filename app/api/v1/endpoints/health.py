from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Verifies API status and database connectivity with pgvector."""
    db_status = "healthy"
    pgvector_status = "disabled"
    try:
        # Check basic query
        await db.execute(text("SELECT 1;"))
        # Check pgvector extension
        res = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
        if res.scalar():
            pgvector_status = "active"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "service": "Sentinel-AI",
        "database": db_status,
        "pgvector": pgvector_status,
        "mode": "electoral_monitoring",
    }
