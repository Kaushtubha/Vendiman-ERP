"""
app/repositories/base.py — Generic Base Repository

PATTERN: Repository Pattern with Generic type parameter.

WHY the Repository Pattern:
    1. DECOUPLING: Service layer calls repository.get_by_id() — it doesn't
       know or care whether data comes from Postgres, MongoDB, or an in-memory
       dict. Switching databases requires only a new repository implementation.

    2. TESTABILITY: In unit tests, inject a mock repository. Services are
       tested without a real database — orders of magnitude faster.

    3. SINGLE RESPONSIBILITY: Repositories are the ONLY place that imports
       SQLAlchemy. Services never write raw SQL or ORM queries.

    4. QUERY REUSE: Common queries (get_by_id, get_all with filters) are
       defined once here. Subclasses inherit them.

WHY Generic[ModelType]:
    The base repository is parameterized by model type (e.g., BaseRepository[Product]).
    This gives type safety and IDE completion in subclasses — get_by_id() returns
    Product, not Any.

ALTERNATIVE CONSIDERED: Active Record (Django ORM style) — rejected because
    it couples the model to the DB query logic, making models harder to test
    and impossible to reuse across different storage backends.

SCALABILITY:
    - Soft delete: All repositories use `deleted_at IS NULL` in every query.
      Deleted records remain in the DB for audit trail — hard delete is never used.
    - Optimistic locking: Subclasses for inventory models add version checks
      to UPDATE statements to prevent lost updates under concurrent access.
    - Async: All methods are coroutines. 0 blocking I/O — fully non-blocking.

DATABASE OPTIMIZATION:
    - execute() + scalars(): SQLAlchemy 2.0 style. Returns typed results.
    - selectinload() in subclasses: Eager-load related models in one query
      (avoids N+1 selects). Usage: options(selectinload(Product.category))
    - OFFSET pagination: Acceptable for this system's scale. At > 1M rows,
      switch to keyset/cursor pagination in the specific list query.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository providing standard CRUD operations.

    All repositories in the application MUST extend this class.
    Subclasses override model_class and add domain-specific queries.

    Attributes:
        model_class: The SQLAlchemy model class this repository manages.
        session: The async database session for this request's Unit of Work.
    """

    model_class: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_select(self) -> Select:
        """
        Return the base SELECT statement for this model.

        Applies soft-delete filter globally — ALL queries exclude deleted records
        by default. Use _base_select_including_deleted() explicitly when needed
        (e.g., audit trail, admin undelete).
        """
        stmt = select(self.model_class)
        if hasattr(self.model_class, "deleted_at"):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]
        return stmt

    async def get_by_id(self, entity_id: UUID | str) -> ModelType | None:
        """
        Fetch a single record by primary key (UUID).

        Returns None if not found or soft-deleted.
        Caller can raise ResourceNotFoundException for HTTP 404.
        """
        stmt = self._base_select().where(
            self.model_class.id == entity_id  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(
        self,
        entity_id: UUID | str,
        resource_name: str | None = None,
    ) -> ModelType:
        """
        Fetch by ID and raise ResourceNotFoundException if not found.

        WHY this convenience method: Eliminates repetitive
        `if not entity: raise ResourceNotFoundException(...)` in service layer.
        Service code becomes: `product = await repo.get_by_id_or_raise(id)`
        """
        from app.core.exceptions import ResourceNotFoundException

        resource_name = resource_name or self.model_class.__name__
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise ResourceNotFoundException(resource_name, str(entity_id))
        return entity

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 25,
        order_by: Any = None,
    ) -> tuple[list[ModelType], int]:
        """
        Fetch a paginated list of records with total count.

        WHY return (list, count) tuple:
            Separate queries for data and count is the standard approach.
            SQLAlchemy 2.0 doesn't support COUNT in the same query as
            LIMIT/OFFSET efficiently. COUNT(*) with subquery is faster for
            large tables than COUNT with ORDER BY.

        Returns:
            Tuple of (records, total_count)
        """
        # Count query (no ORDER BY — unnecessary for counting)
        count_stmt = select(func.count()).select_from(
            self._base_select().subquery()
        )
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Data query
        data_stmt = self._base_select().offset(offset).limit(limit)
        if order_by is not None:
            data_stmt = data_stmt.order_by(order_by)

        data_result = await self.session.execute(data_stmt)
        records = list(data_result.scalars().all())

        return records, total

    async def create(self, entity: ModelType) -> ModelType:
        """
        Persist a new entity to the database.

        WHY no explicit commit: Commits are the responsibility of the service
        layer (or the get_db() dependency on success). The repository only
        adds to the session's pending changes — the Unit of Work commits atomically.
        """
        self.session.add(entity)
        await self.session.flush()  # Flush assigns DB-generated values (UUID, timestamps)
        await self.session.refresh(entity)
        logger.debug(
            "Created %s id=%s",
            self.model_class.__name__,
            getattr(entity, "id", "unknown"),
        )
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """
        Update an existing entity.

        WHY session.merge() is NOT used: merge() triggers a SELECT before UPDATE.
        We already have the entity loaded — just flush changes.
        """
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def soft_delete(self, entity: ModelType) -> None:
        """
        Soft-delete an entity by setting deleted_at timestamp.

        WHY soft delete (not hard delete):
            - Audit trail: Know what was deleted and when.
            - Recovery: Accidental deletes can be reversed (clear deleted_at).
            - Referential integrity: Related records can still reference the ID.
            - Reports: Historical reports include data from deleted records.

        Hard delete is only used for GDPR "right to be forgotten" requests,
        handled by a separate admin-only endpoint with audit logging.
        """
        if not hasattr(entity, "deleted_at"):
            raise AttributeError(
                f"{self.model_class.__name__} does not support soft delete "
                f"(missing deleted_at column)"
            )
        entity.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        await self.session.flush()
        logger.info(
            "Soft-deleted %s id=%s",
            self.model_class.__name__,
            getattr(entity, "id", "unknown"),
        )

    async def bulk_create(self, entities: list[ModelType]) -> list[ModelType]:
        """
        Insert multiple entities in a single flush.

        WHY: Inserting 100 products one-by-one = 100 round trips to DB.
        Batch insert = 1 round trip. Used in Excel import endpoints.

        SCALABILITY: For very large imports (> 10k rows), use
        session.execute(insert(Model).values([...]))  — bulk INSERT without
        ORM overhead. Trade-off: no after-insert hooks.
        """
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities

    async def exists(self, **filters: Any) -> bool:
        """Check if a record matching the given filters exists."""
        stmt = select(func.count()).select_from(self.model_class)
        if hasattr(self.model_class, "deleted_at"):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))  # type: ignore[attr-defined]
        for field, value in filters.items():
            stmt = stmt.where(
                getattr(self.model_class, field) == value
            )
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0
