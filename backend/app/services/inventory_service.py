"""
app/services/inventory_service.py — Inventory Business Logic
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientStockException, ResourceNotFoundException, ValidationException
from app.domain.enums import InventoryAdjustmentReason, InventoryTransactionType
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)

    async def list_stocks(
        self,
        offset: int = 0,
        limit: int = 25,
        warehouse_id: uuid.UUID | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> tuple[list[dict], int]:
        return await self.repo.list_stocks(
            offset=offset,
            limit=limit,
            warehouse_id=warehouse_id,
            search=search,
            low_stock_only=low_stock_only,
        )

    async def adjust_stock(
        self,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        new_quantity: int,
        reason: str,
        performed_by_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> dict:
        if new_quantity < 0:
            raise ValidationException("Stock quantity cannot be negative", field="new_quantity")

        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ResourceNotFoundException("Product", str(product_id))

        stock = await self.repo.get_or_create_stock(product_id, warehouse_id)
        qty_before = stock.quantity_on_hand
        qty_change = new_quantity - qty_before

        stock.quantity_on_hand = new_quantity

        # Record transaction in immutable ledger
        tx_type = (
            InventoryTransactionType.MANUAL_ADJUSTMENT_IN
            if qty_change >= 0
            else InventoryTransactionType.MANUAL_ADJUSTMENT_OUT
        )

        await self.repo.record_transaction(
            product_id=product_id,
            warehouse_id=warehouse_id,
            transaction_type=tx_type,
            quantity_change=qty_change,
            quantity_before=qty_before,
            quantity_after=new_quantity,
            unit_cost=product.cost_price,
            performed_by_id=performed_by_id,
            reference_type="manual_adjustment",
            reason=reason,
            notes=notes,
        )

        logger.info(
            "Stock adjusted for product=%s warehouse=%s from %d to %d (change: %+d)",
            product.sku,
            warehouse_id,
            qty_before,
            new_quantity,
            qty_change,
        )

        return {
            "product_id": str(product_id),
            "warehouse_id": str(warehouse_id),
            "quantity_before": qty_before,
            "quantity_after": new_quantity,
            "quantity_change": qty_change,
        }

    async def list_transactions(
        self,
        offset: int = 0,
        limit: int = 25,
        product_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        transaction_type: str | None = None,
    ) -> tuple[list[dict], int]:
        return await self.repo.list_transactions(
            offset=offset,
            limit=limit,
            product_id=product_id,
            warehouse_id=warehouse_id,
            transaction_type=transaction_type,
        )

    async def get_expiring_stock(self, days_threshold: int = 30) -> list[dict]:
        return await self.repo.list_expiring_batches(days_threshold=days_threshold)
