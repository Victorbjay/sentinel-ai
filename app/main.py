from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and extensions on application startup."""
    try:
        await init_db()
    except Exception as e:
        print(f"[Warning] Failed to initialize DB during lifespan: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sentinel-AI: Real-Time Electoral Misinformation & Narrative Monitoring Engine (#AI4Elections Hackathon Track 1)",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": "Sentinel-AI",
        "description": "Automated Electoral Narrative & Misinformation Intelligence Engine",
        "track": "Track 1: AI and Trustworthy Electoral Information",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
    }
