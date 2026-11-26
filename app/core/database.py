from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base model class with automatic naming conventions."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize pgvector extension, create tables, and apply lightweight vector column migrations."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        # Ensure vector columns exist if upgrading an existing database volume
        dim = settings.EMBEDDING_DIMENSION
        await conn.execute(text(f"ALTER TABLE claims ADD COLUMN IF NOT EXISTS embedding vector({dim});"))
        await conn.execute(text("ALTER TABLE claims ADD COLUMN IF NOT EXISTS spread_score INTEGER DEFAULT 0;"))
        await conn.execute(text("ALTER TABLE claims ADD COLUMN IF NOT EXISTS synthetic_media_attached BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE claims ADD COLUMN IF NOT EXISTS triage_priority FLOAT DEFAULT 0.0;"))
        await conn.execute(text(f"ALTER TABLE narratives ADD COLUMN IF NOT EXISTS centroid_embedding vector({dim});"))
