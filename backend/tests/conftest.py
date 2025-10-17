"""
Shared pytest configuration for all tests.

Manages test database lifecycle and provides shared fixtures.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from pathlib import Path

from app.db.config import init_db, close_db, engine
from sqlmodel import SQLModel


# Set testing environment variable
os.environ["TESTING"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.

    This prevents "Event loop is closed" errors in async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Setup test database before all tests and tear down after.

    This fixture:
    - Creates the test database file (thurup_test.db)
    - Initializes all tables
    - Yields for tests to run
    - Cleans up the database after all tests complete
    """
    # Get test database path
    test_db_path = Path("thurup_test.db")

    # Remove existing test database if it exists
    if test_db_path.exists():
        test_db_path.unlink()

    # Initialize database tables
    await init_db()

    yield

    # Cleanup: close connections and remove test database
    await close_db()
    if test_db_path.exists():
        test_db_path.unlink()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """
    Clean all tables between tests for isolation.

    This fixture runs before each test to ensure a clean slate.
    """
    # This runs before each test
    yield

    # After each test, truncate all tables (but keep schema)
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(SQLModel.metadata.drop_all)
        # Recreate all tables
        await conn.run_sync(SQLModel.metadata.create_all)
