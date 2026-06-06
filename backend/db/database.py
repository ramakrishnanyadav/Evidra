from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel
from core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # Enable pgvector extension before creating tables
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
        
        # Create IVFFlat index for fast approximate nearest neighbor search
        # lists=100 is appropriate for up to 1 million vectors
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_candidate_embedding 
            ON candidates 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))
        
        # Existing JSONB indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_candidate_skills 
            ON candidates USING GIN (extracted_skills jsonb_path_ops)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_candidate_recommendation 
            ON candidates (recommendation, organization_id, created_at DESC)
        """))
        
        logger.info("Database initialized successfully.")

async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
