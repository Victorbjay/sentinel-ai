from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


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

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def dashboard():
    """Serves the low-bandwidth Sentinel-AI Observer & Fact-Checker Console."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"project": "Sentinel-AI", "docs_url": "/docs"}


@app.get("/api/v1/info", tags=["Root"])
async def root_info():
    return {
        "project": "Sentinel-AI",
        "description": "Automated Electoral Narrative & Misinformation Intelligence Engine",
        "track": "Track 1: AI and Trustworthy Electoral Information",
        "dashboard_url": "/",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
    }
