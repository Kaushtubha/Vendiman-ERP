"""
tests/conftest.py — Pytest Fixtures & Test Configuration

PATTERN: Shared pytest fixtures with proper async support and DB isolation.

WHY separate test DB (not production DB):
    Tests MUST be isolated. Running against a real DB would:
    1. Corrupt production data on `INSERT` tests
    2. Be non-deterministic (test order matters if data bleeds between tests)
    3. Make tests slow (real network round trips)

ISOLATION STRATEGY:
    - Each test gets a fresh database transaction.
    - The transaction is ROLLED BACK after each test — no cleanup code needed.
    - This gives each test a clean slate without recreating the schema.

    WHY rollback (not truncate/drop-recreate):
        - ROLLBACK is O(1) — instantaneous regardless of data volume.
        - DROP/CREATE TABLE requires schema privileges and rebuilds indexes.
        - TRUNCATE still leaves audit records and doesn't test constraint violations.

FIXTURE SCOPING:
    - session scope: DB schema created once per test run (expensive)
    - function scope: Transaction per test (default, fast)
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.core.dependencies import get_db
from app.main import app

# Test database URL — use SQLite in-memory for fast unit tests
# For integration tests, use a real test Postgres DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a single event loop for the entire test session.

    WHY session scope: Creating a new event loop per test is expensive.
    pytest-asyncio's default (function scope) can cause issues with
    session-scoped async fixtures.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async test DB engine and schema once per session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a test database session with automatic rollback.

    Each test function gets a fresh session that is rolled back after
    the test completes — ensuring test isolation.
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with test_engine.connect() as conn:
        await conn.begin()
        async with async_session(bind=conn) as session:
            yield session
        await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async test client with DB session override.

    Overrides the `get_db` dependency to use the test session.
    This ensures test HTTP requests use the same rollback-wrapped session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
