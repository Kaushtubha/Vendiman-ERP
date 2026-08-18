"""
app/repositories/inventory_repository.py — Inventory Data Access Layer
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.inventory import InventoryBatch, InventoryStock, InventoryTransaction
from app.domain.models.product import Product
from app.domain.models.warehouse import Warehouse


class InventoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Stock Balance (inventory_stocks) ──────────────────────────────────────

    async def get_stock(self, product_id: uuid.UUID, warehouse_id: uuid.UUID) -> InventoryStock | None:
        result = await self.db.execute(
            select(InventoryStock).where(
                InventoryStock.product_id == product_id,
                InventoryStock.warehouse_id == warehouse_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_stock(self, product_id: uuid.UUID, warehouse_id: uuid.UUID) -> InventoryStock:
        stock = await self.get_stock(product_id, warehouse_id)
        if not stock:
            stock = InventoryStock(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                quantity_damaged=0,
                average_cost_price=Decimal("0.00"),
            )
            self.db.add(stock)
            await self.db.flush()
            await self.db.refresh(stock)
        return stock

    async def list_stocks(
        self,
        offset: int = 0,
        limit: int = 25,
        warehouse_id: uuid.UUID | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> tuple[list[dict], int]:
        query = (
            select(InventoryStock, Product, Warehouse)
            .join(Product, Product.id == InventoryStock.product_id)
            .join(Warehouse, Warehouse.id == InventoryStock.warehouse_id)
        )
        count_query = (
            select(func.count(InventoryStock.id))
            .join(Product, Product.id == InventoryStock.product_id)
            .join(Warehouse, Warehouse.id == InventoryStock.warehouse_id)
        )

        if warehouse_id:
            query = query.where(InventoryStock.warehouse_id == warehouse_id)
            count_query = count_query.where(InventoryStock.warehouse_id == warehouse_id)

        if search:
            pattern = f"%{search}%"
            condition = or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        if low_stock_only:
            condition = InventoryStock.quantity_on_hand <= Product.reorder_point
            query = query.where(condition)
            count_query = count_query.where(condition)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(Product.name).offset(offset).limit(limit)
        )
        rows = result.all()
        items = []
        for stock, product, warehouse in rows:
            items.append({
                "id": str(stock.id),
                "product_id": str(product.id),
                "product_sku": product.sku,
                "product_name": product.name,
                "product_mrp": float(product.mrp),
                "product_cost_price": float(product.cost_price),
                "product_selling_price": float(product.selling_price),
                "warehouse_id": str(warehouse.id),
                "warehouse_name": warehouse.name,
                "warehouse_code": warehouse.code,
                "quantity_on_hand": stock.quantity_on_hand,
                "quantity_reserved": stock.quantity_reserved,
                "quantity_damaged": stock.quantity_damaged,
                "available_quantity": stock.available_quantity,
                "reorder_point": product.reorder_point,
                "is_low_stock": stock.quantity_on_hand <= product.reorder_point,
                "updated_at": stock.updated_at.isoformat() if stock.updated_at else None,
            })
        return items, total

    # ── Transactions Ledger ───────────────────────────────────────────────────

    async def record_transaction(
        self,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        transaction_type: str,
        quantity_change: int,
        quantity_before: int,
        quantity_after: int,
        unit_cost: Decimal = Decimal("0.00"),
        performed_by_id: uuid.UUID | None = None,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> InventoryTransaction:
        tx = InventoryTransaction(
            product_id=product_id,
            warehouse_id=warehouse_id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            unit_cost=unit_cost,
            performed_by_id=performed_by_id,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
            notes=notes,
        )
        self.db.add(tx)
        await self.db.flush()
        return tx

    async def list_transactions(
        self,
        offset: int = 0,
        limit: int = 25,
        product_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
    ) -> tuple[list[dict], int]:
        query = (
            select(InventoryTransaction, Product, Warehouse)
            .join(Product, Product.id == InventoryTransaction.product_id)
            .join(Warehouse, Warehouse.id == InventoryTransaction.warehouse_id)
        )
        count_query = select(func.count(InventoryTransaction.id))

        if product_id:
            query = query.where(InventoryTransaction.product_id == product_id)
            count_query = count_query.where(InventoryTransaction.product_id == product_id)
        if warehouse_id:
            query = query.where(InventoryTransaction.warehouse_id == warehouse_id)
            count_query = count_query.where(InventoryTransaction.warehouse_id == warehouse_id)
        if transaction_type:
            query = query.where(InventoryTransaction.transaction_type == transaction_type)
            count_query = count_query.where(InventoryTransaction.transaction_type == transaction_type)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one()

        result = await self.db.execute(
            query.order_by(InventoryTransaction.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.all()
        items = []
        for tx, prod, wh in rows:
            items.append({
                "id": str(tx.id),
                "product_id": str(prod.id),
                "product_name": prod.name,
                "product_sku": prod.sku,
                "warehouse_id": str(wh.id),
                "warehouse_name": wh.name,
                "transaction_type": tx.transaction_type,
                "quantity_change": tx.quantity_change,
                "quantity_before": tx.quantity_before,
                "quantity_after": tx.quantity_after,
                "unit_cost": float(tx.unit_cost),
                "reference_type": tx.reference_type,
                "reference_id": str(tx.reference_id) if tx.reference_id else None,
                "reason": tx.reason,
                "notes": tx.notes,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            })
        return items, total

    # ── Batches ───────────────────────────────────────────────────────────────

    async def list_expiring_batches(self, days_threshold: int = 30) -> list[dict]:
        from datetime import date, timedelta
        target_date = date.today() + timedelta(days=days_threshold)
        query = (
            select(InventoryBatch, Product, Warehouse)
            .join(Product, Product.id == InventoryBatch.product_id)
            .join(Warehouse, Warehouse.id == InventoryBatch.warehouse_id)
            .where(
                InventoryBatch.expiry_date <= target_date,
                InventoryBatch.quantity_remaining > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc())
        )
        result = await self.db.execute(query)
        rows = result.all()
        items = []
        for batch, prod, wh in rows:
            days_left = (batch.expiry_date - date.today()).days if batch.expiry_date else None
            items.append({
                "id": str(batch.id),
                "batch_number": batch.batch_number,
                "product_id": str(prod.id),
                "product_name": prod.name,
                "product_sku": prod.sku,
                "warehouse_id": str(wh.id),
                "warehouse_name": wh.name,
                "quantity_remaining": batch.quantity_remaining,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "days_until_expiry": days_left,
                "is_expired": days_left is not None and days_left <= 0,
            })
        return items
