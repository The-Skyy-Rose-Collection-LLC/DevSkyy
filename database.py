"""
Enterprise Database Configuration - SQLAlchemy Support
Production-ready with Neon, Supabase, PlanetScale support
"""

import logging
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from database_config import CONNECTION_ARGS, DATABASE_URL

logger = logging.getLogger(__name__)

# Create async engine with production-ready configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False") == "True",
    future=True,
    **CONNECTION_ARGS,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # Use db here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections.
    Call this on application shutdown.
    """
    await engine.dispose()


# For backward compatibility with MongoDB code
class DatabaseManager:
    """
    Compatibility layer for existing MongoDB code.
    Provides similar interface to Motor/PyMongo.
    """

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self.connected = False

    async def connect(self):
        """Initialize database connection"""
        try:
            await init_db()
            self.connected = True
            return {"status": "connected", "type": "SQLAlchemy", "url": DATABASE_URL}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def disconnect(self):
        """Close database connection"""
        await close_db()
        self.connected = False

    async def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return AsyncSessionLocal()

    def get_database(self):
        """For compatibility - returns self"""
        return self

    async def health_check(self):
        """Check database health"""
        try:
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "connected": True,
                    "type": "SQLAlchemy",
                    "url": (
                        DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "sqlite"
                    ),
                }
        except Exception as e:
            return {"status": "unhealthy", "connected": False, "error": str(e)}


# Global database instance
db_manager = DatabaseManager()
