"""
app/repositories/grn_repository.py — Goods Receipt Note Data Access Layer
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.grn import GoodsReceiptNote, GRNLineItem
from app.domain.models.product import Product
from app.domain.models.purchase_order import PurchaseOrder
from app.domain.models.warehouse import Warehouse


class GRNRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, grn_id: uuid.UUID) -> GoodsReceiptNote | None:
        result = await self.db.execute(
            select(GoodsReceiptNote)
            .options(
                selectinload(GoodsReceiptNote.line_items).selectinload(GRNLineItem.product),
                selectinload(GoodsReceiptNote.purchase_order),
                selectinload(GoodsReceiptNote.warehouse),
            )
            .where(GoodsReceiptNote.id == grn_id)
        )
        return result.scalar_one_or_none()

    async def list_grns(
        self,
        offset: int = 0,
        limit: int = 25,
        warehouse_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[GoodsReceiptNote], int]:
        query = (
            select(GoodsReceiptNote)
            .options(
                selectinload(GoodsReceiptNote.purchase_order),
                selectinload(GoodsReceiptNote.warehouse),
            )
        )
        count_query = select(func.count(GoodsReceiptNote.id))

        if warehouse_id:
            query = query.where(GoodsReceiptNote.warehouse_id == warehouse_id)
            count_query = count_query.where(GoodsReceiptNote.warehouse_id == warehouse_id)
        if status:
            query = query.where(GoodsReceiptNote.status == status)
            count_query = count_query.where(GoodsReceiptNote.status == status)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one()

        result = await self.db.execute(
            query.order_by(GoodsReceiptNote.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> GoodsReceiptNote:
        grn = GoodsReceiptNote(**kwargs)
        self.db.add(grn)
        await self.db.flush()
        await self.db.refresh(grn)
        return grn

    async def add_line_item(self, **kwargs: Any) -> GRNLineItem:
        item = GRNLineItem(**kwargs)
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_status(self, grn_id: uuid.UUID, status: str, **kwargs: Any) -> None:
        await self.db.execute(
            update(GoodsReceiptNote)
            .where(GoodsReceiptNote.id == grn_id)
            .values(status=status, **kwargs)
        )

    async def generate_grn_number(self) -> str:
        import shortuuid
        prefix = f"GRN-{date.today().strftime('%Y%m')}"
        suffix = shortuuid.uuid()[:6].upper()
        return f"{prefix}-{suffix}"
