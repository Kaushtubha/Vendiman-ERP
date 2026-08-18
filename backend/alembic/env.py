"""
alembic/env.py — Alembic Migration Environment

CRITICAL: This file bridges Alembic with our SQLAlchemy models.

HOW IT WORKS:
    1. Imports app.core.database.Base — this triggers all model imports
       (which register their tables with Base.metadata).
    2. Passes Base.metadata to alembic's context.configure().
    3. Alembic diffs current metadata vs database schema to generate migrations.

WHY we import all models explicitly:
    SQLAlchemy's Base.metadata only knows about models that have been IMPORTED.
    If a model module is never imported, its table is invisible to autogenerate.
    The `import_all_models()` function ensures all models are imported.

ASYNC vs SYNC:
    Alembic's default env.py is synchronous.
    For our async SQLAlchemy setup, we use asyncio.run() to execute the
    migration within an event loop.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import Application Configuration ─────────────────────────────────────────
from app.core.config import get_settings
from app.core.database import Base

settings = get_settings()


def import_all_models() -> None:
    """
    Import all ORM model modules to register them with Base.metadata.

    WHY: Python's metaclass system registers models when they're imported.
    Alembic's autogenerate only sees models that have been imported into
    the Python process. This function ensures all models are imported
    before Alembic inspects Base.metadata.

    Add new model modules here as they are created.
    """
    # Import all domain models so they register with Base.metadata.
    # Alembic autogenerate only sees models that have been imported.
    import app.domain.models  # noqa: F401 — triggers __init__.py which imports all models


# Import all models before Alembic reads metadata
import_all_models()

# Alembic config object
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the MetaData object Alembic autogenerates migrations from
target_metadata = Base.metadata


def get_url() -> str:
    """
    Return the SYNCHRONOUS database URL for Alembic.

    Alembic needs a sync driver (psycopg2) even though the application
    uses async (asyncpg). The sync URL is derived from the async URL.
    """
    return settings.database.sync_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    WHY offline mode: Generates SQL scripts without connecting to the database.
    Used to produce migration SQL for DBA review before applying in production.
    Useful when the application doesn't have direct DB access (e.g., RDS
    behind VPC — only the DBA machine can access it).

    Usage: alembic upgrade head --sql > migration.sql
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,       # Detect column type changes
        compare_server_default=True,  # Detect default value changes
        render_as_batch=True,    # SQLite-compatible (useful for local testing)
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure and run migrations with a live DB connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # WHY include_schemas=False: We use one schema (public). Set to True
        # if multi-schema support is needed (e.g., per-tenant schema isolation).
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with an async engine.

    WHY asyncio: Our application uses asyncpg. Alembic needs a sync
    connection, but we construct the async engine from config and use
    `run_sync` to run the synchronous `do_run_migrations` within the
    async context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling during migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
