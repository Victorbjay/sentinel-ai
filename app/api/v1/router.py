from fastapi import APIRouter
from app.api.v1.endpoints import health, claims, narratives, facts, reviews, simulate

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(claims.router, prefix="/claims", tags=["Claims & Ingestion"])
api_router.include_router(narratives.router, prefix="/narratives", tags=["Narratives & Clusters"])
api_router.include_router(facts.router, prefix="/facts", tags=["Verified Facts & Vector RAG"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Human-in-the-Loop Review"])
api_router.include_router(simulate.router, prefix="/simulate", tags=["Election-Day Simulator"])
