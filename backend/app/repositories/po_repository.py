"""
app/repositories/po_repository.py — Purchase Order Data Access Layer
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.product import Product
from app.domain.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from app.domain.models.supplier import Supplier
from app.domain.models.warehouse import Warehouse


class PurchaseOrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, po_id: uuid.UUID) -> PurchaseOrder | None:
        result = await self.db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.line_items).selectinload(PurchaseOrderLineItem.product),
                selectinload(PurchaseOrder.supplier),
                selectinload(PurchaseOrder.warehouse),
            )
            .where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, po_number: str) -> PurchaseOrder | None:
        result = await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )
        return result.scalar_one_or_none()

    async def list_pos(
        self,
        offset: int = 0,
        limit: int = 25,
        supplier_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[PurchaseOrder], int]:
        query = (
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.supplier),
                selectinload(PurchaseOrder.warehouse),
            )
        )
        count_query = select(func.count(PurchaseOrder.id))

        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
            count_query = count_query.where(PurchaseOrder.supplier_id == supplier_id)
        if warehouse_id:
            query = query.where(PurchaseOrder.warehouse_id == warehouse_id)
            count_query = count_query.where(PurchaseOrder.warehouse_id == warehouse_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
            count_query = count_query.where(PurchaseOrder.status == status)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one()

        result = await self.db.execute(
            query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> PurchaseOrder:
        po = PurchaseOrder(**kwargs)
        self.db.add(po)
        await self.db.flush()
        await self.db.refresh(po)
        return po

    async def add_line_item(self, **kwargs: Any) -> PurchaseOrderLineItem:
        item = PurchaseOrderLineItem(**kwargs)
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_status(self, po_id: uuid.UUID, status: str, **kwargs: Any) -> None:
        await self.db.execute(
            update(PurchaseOrder)
            .where(PurchaseOrder.id == po_id)
            .values(status=status, **kwargs)
        )

    async def generate_po_number(self) -> str:
        import shortuuid
        prefix = f"PO-{date.today().strftime('%Y%m')}"
        suffix = shortuuid.uuid()[:6].upper()
        return f"{prefix}-{suffix}"
