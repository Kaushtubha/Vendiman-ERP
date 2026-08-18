"""
app/core/database.py — Async Database Engine & Session Management

PATTERN: SQLAlchemy 2.0 async engine with session factory and Unit of Work.

ARCHITECTURAL DECISIONS:

1. WHY SQLAlchemy 2.0 async (not sync):
   FastAPI is built on Starlette/asyncio. Synchronous DB calls block the
   event loop — under concurrent load, 100 blocking 50ms queries become
   5 seconds of stall time. Async I/O keeps the loop free to handle other
   requests during DB wait time.

2. WHY asyncpg driver (not psycopg3):
   asyncpg is a pure-async, protocol-level PostgreSQL driver written in
   Cython. In benchmarks, asyncpg processes 2-5x more queries/second than
   psycopg3 for read-heavy workloads. It has been production-tested at
   Uber, Edgedb, and several fintech companies.

3. WHY connection pooling (not per-request connections):
   Opening a new TCP connection to Postgres costs ~10-50ms (TCP handshake +
   SSL negotiation + auth). With a pool of 20 connections, all 4 workers
   share pre-warmed connections. Under 100 req/s, this saves ~1-5 seconds
   of latency per second of throughput.

4. WHY AsyncSession (not Session):
   Prevents blocking the event loop. SQLAlchemy's async session wraps all
   operations in coroutines, allowing the event loop to do other work while
   waiting for the database.

5. UNIT OF WORK PATTERN:
   Each request gets its own session (via get_db dependency). The session
   tracks all entity changes within the request. On commit, all changes
   are written atomically. On exception, all changes are rolled back.
   This ensures data consistency without manual transaction management.

SCALABILITY:
   - Pool size: 20 connections × 4 workers = 80 max connections from this
     service. Set Postgres max_connections = 100 in dev, 500+ in production.
   - pool_recycle=1800: Prevents "server closed the connection unexpectedly"
     errors after the DB firewall's TCP idle timeout.
   - For read replicas: create a separate read engine pointing to the
     replica URL and use it in repository read methods.

OPTIMIZATION:
   - expire_on_commit=False: Prevents SQLAlchemy from expiring all loaded
     attributes after commit, avoiding lazy-load N+1 queries on the
     response serialization step.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all ORM models.

    WHY centralized Base: All models must inherit from this single Base.
    Alembic's autogenerate scans Base.metadata to detect schema changes.
    If models use different bases, migrations miss tables.

    All models register themselves here via their class definitions —
    Python's metaclass mechanism handles the registration automatically.
    No explicit registration required.
    """

    pass


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """
    Create and configure the async SQLAlchemy engine.

    Separated from module-level initialization to allow test overrides —
    tests can call create_engine() with a test database URL.

    Args:
        database_url: Override URL (used in tests). Defaults to settings URL.

    Returns:
        Configured AsyncEngine instance.
    """
    settings = get_settings()
    url = database_url or settings.database.url
    db = settings.database

    # NullPool for test environments prevents connection leaks between tests.
    # Production uses QueuePool (SQLAlchemy default for async engines).
    pool_class = NullPool if settings.is_development and "pytest" in url else None

    engine_kwargs: dict = {
        "echo": db.echo,
        "pool_pre_ping": True,     # Verify connections are alive before using them
        "pool_recycle": db.pool_recycle,
    }

    if pool_class:
        engine_kwargs["poolclass"] = pool_class
    else:
        engine_kwargs.update({
            "pool_size": db.pool_size,
            "max_overflow": db.max_overflow,
            "pool_timeout": db.pool_timeout,
        })

    engine = create_async_engine(url, **engine_kwargs)

    logger.info(
        "Database engine created: host=%s pool_size=%s",
        url.split("@")[-1] if "@" in url else url,  # Never log credentials
        db.pool_size,
    )

    return engine


# Module-level engine — created once per process
engine: AsyncEngine = create_engine()

# Session factory — NOT a session, just a factory.
# Calling AsyncSessionLocal() creates a new session.
# WHY async_sessionmaker: Type-safe factory that yields AsyncSession instances
# with the configured options. autocommit=False means we control transactions.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # See docstring above
    autocommit=False,
    autoflush=False,         # Explicit flush = predictable SQL execution order
)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Used directly in Celery tasks and other non-FastAPI contexts where
    the FastAPI dependency injection system is not available.

    Usage:
        async with get_async_session() as session:
            result = await session.execute(stmt)
            await session.commit()
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


async def check_database_connection() -> bool:
    """
    Verify database connectivity. Used in health check endpoints.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False
