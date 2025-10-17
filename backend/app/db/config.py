"""
Database configuration and session management using SQLModel.

Provides async SQLModel/SQLAlchemy engine and session factory for SQLite database.
"""

import os
import sys
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.logging_config import get_logger

logger = get_logger(__name__)

# Detect if running in test mode
IS_TEST = "pytest" in sys.modules or os.getenv("TESTING") == "true"

# Database configuration from environment
# Use separate test database when running tests
if IS_TEST:
    DEFAULT_DB = "sqlite+aiosqlite:///./thurup_test.db"
else:
    DEFAULT_DB = "sqlite+aiosqlite:///./thurup.db"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=DATABASE_ECHO,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
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
    Initialize database tables.

    Creates all tables defined in SQLModel models if they don't exist.
    Should be called on application startup.
    """
    # Import models to register them with SQLModel

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("database_initialized", database_url=DATABASE_URL)


async def close_db():
    """
    Close database connections.

    Should be called on application shutdown.
    """
    await engine.dispose()
    logger.info("database_closed")
