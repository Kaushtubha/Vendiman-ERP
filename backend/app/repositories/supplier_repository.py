"""
app/repositories/supplier_repository.py — Supplier Data Access Layer
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.supplier import Supplier


class SupplierRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, supplier_id: uuid.UUID) -> Supplier | None:
        result = await self.db.execute(select(Supplier).where(Supplier.id == supplier_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Supplier | None:
        result = await self.db.execute(select(Supplier).where(Supplier.code == code.upper()))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 25,
        search: str | None = None,
        status: str | None = None,
        rating: str | None = None,
    ) -> tuple[list[Supplier], int]:
        query = select(Supplier)
        count_query = select(func.count(Supplier.id))

        if search:
            pattern = f"%{search}%"
            condition = or_(
                Supplier.name.ilike(pattern),
                Supplier.code.ilike(pattern),
                Supplier.email.ilike(pattern),
                Supplier.phone.ilike(pattern),
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        if status:
            query = query.where(Supplier.status == status)
            count_query = count_query.where(Supplier.status == status)

        if rating:
            query = query.where(Supplier.rating == rating)
            count_query = count_query.where(Supplier.rating == rating)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Supplier.name).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> Supplier:
        if "code" in kwargs:
            kwargs["code"] = kwargs["code"].upper()
        supplier = Supplier(**kwargs)
        self.db.add(supplier)
        await self.db.flush()
        await self.db.refresh(supplier)
        return supplier

    async def update(self, supplier_id: uuid.UUID, **kwargs: Any) -> Supplier | None:
        if "code" in kwargs:
            kwargs["code"] = kwargs["code"].upper()
        await self.db.execute(update(Supplier).where(Supplier.id == supplier_id).values(**kwargs))
        return await self.get_by_id(supplier_id)

    async def exists_by_code(self, code: str, exclude_id: uuid.UUID | None = None) -> bool:
        from sqlalchemy import exists as sql_exists
        query = select(sql_exists().where(Supplier.code == code.upper()))
        if exclude_id:
            query = select(sql_exists().where(Supplier.code == code.upper(), Supplier.id != exclude_id))
        result = await self.db.execute(query)
        return result.scalar_one()
