"""
app/repositories/product_repository.py — Product Data Access Layer
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.product import Product, ProductCategory


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Categories ────────────────────────────────────────────────────────────

    async def get_all_categories(self) -> list[ProductCategory]:
        result = await self.db.execute(
            select(ProductCategory).where(ProductCategory.is_active == True).order_by(ProductCategory.name)  # noqa: E712
        )
        return list(result.scalars().all())

    async def create_category(self, **kwargs: Any) -> ProductCategory:
        cat = ProductCategory(**kwargs)
        self.db.add(cat)
        await self.db.flush()
        await self.db.refresh(cat)
        return cat

    # ── Products ──────────────────────────────────────────────────────────────

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.sku == sku.upper()))
        return result.scalar_one_or_none()

    async def get_by_barcode(self, barcode: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.barcode == barcode))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 25,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        status: str | None = None,
        is_perishable: bool | None = None,
    ) -> tuple[list[Product], int]:
        query = select(Product)
        count_query = select(func.count(Product.id))

        if search:
            pattern = f"%{search}%"
            condition = or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.barcode.ilike(pattern),
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        if category_id:
            query = query.where(Product.category_id == category_id)
            count_query = count_query.where(Product.category_id == category_id)

        if status:
            query = query.where(Product.status == status)
            count_query = count_query.where(Product.status == status)

        if is_perishable is not None:
            query = query.where(Product.is_perishable == is_perishable)
            count_query = count_query.where(Product.is_perishable == is_perishable)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Product.name).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> Product:
        if "sku" in kwargs:
            kwargs["sku"] = kwargs["sku"].upper()
        product = Product(**kwargs)
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: uuid.UUID, **kwargs: Any) -> Product | None:
        if "sku" in kwargs:
            kwargs["sku"] = kwargs["sku"].upper()
        await self.db.execute(update(Product).where(Product.id == product_id).values(**kwargs))
        return await self.get_by_id(product_id)

    async def exists_by_sku(self, sku: str, exclude_id: uuid.UUID | None = None) -> bool:
        from sqlalchemy import exists as sql_exists
        query = select(sql_exists().where(Product.sku == sku.upper()))
        if exclude_id:
            query = select(sql_exists().where(Product.sku == sku.upper(), Product.id != exclude_id))
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_below_reorder_point(self, warehouse_id: uuid.UUID) -> list[dict]:
        """Products where stock < reorder_point in the given warehouse."""
        from app.domain.models.inventory import InventoryStock
        result = await self.db.execute(
            select(Product, InventoryStock)
            .join(InventoryStock, InventoryStock.product_id == Product.id)
            .where(
                InventoryStock.warehouse_id == warehouse_id,
                InventoryStock.quantity_on_hand <= Product.reorder_point,
            )
            .order_by(InventoryStock.quantity_on_hand)
        )
        rows = result.all()
        return [
            {
                "product": row[0],
                "stock": row[1],
            }
            for row in rows
        ]
