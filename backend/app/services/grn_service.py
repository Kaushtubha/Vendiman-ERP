"""
app/services/grn_service.py — Goods Receipt Note Business Logic

KEY INVARIANT: Completing a GRN automatically credits physical inventory,
writes to the immutable inventory ledger, creates batch tracking entries,
and updates the parent Purchase Order's received quantities.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationException, ResourceNotFoundException
from app.domain.enums import GRNStatus, InventoryTransactionType, POLineItemStatus, POStatus, StockCondition
from app.domain.models.inventory import InventoryBatch
from app.repositories.grn_repository import GRNRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.po_repository import PurchaseOrderRepository
from app.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class GRNService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GRNRepository(db)
        self.po_repo = PurchaseOrderRepository(db)
        self.inv_repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)

    async def list_grns(
        self,
        offset: int = 0,
        limit: int = 25,
        warehouse_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[dict], int]:
        grns, total = await self.repo.list_grns(
            offset=offset,
            limit=limit,
            warehouse_id=warehouse_id,
            status=status,
        )
        return [
            {
                "id": str(g.id),
                "grn_number": g.grn_number,
                "purchase_order_id": str(g.purchase_order_id),
                "po_number": g.purchase_order.po_number if g.purchase_order else None,
                "warehouse_id": str(g.warehouse_id),
                "warehouse_name": g.warehouse.name if g.warehouse else None,
                "status": g.status,
                "receipt_date": g.receipt_date.isoformat() if g.receipt_date else None,
                "supplier_invoice_number": g.supplier_invoice_number,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in grns
        ], total

    async def get_grn(self, grn_id: uuid.UUID) -> dict:
        g = await self.repo.get_by_id(grn_id)
        if not g:
            raise ResourceNotFoundException("GoodsReceiptNote", str(grn_id))
        return {
            "id": str(g.id),
            "grn_number": g.grn_number,
            "purchase_order_id": str(g.purchase_order_id),
            "po_number": g.purchase_order.po_number if g.purchase_order else None,
            "warehouse_id": str(g.warehouse_id),
            "warehouse_name": g.warehouse.name if g.warehouse else None,
            "status": g.status,
            "receipt_date": g.receipt_date.isoformat() if g.receipt_date else None,
            "supplier_invoice_number": g.supplier_invoice_number,
            "supplier_invoice_date": g.supplier_invoice_date.isoformat() if g.supplier_invoice_date else None,
            "notes": g.notes,
            "line_items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": item.product.name if item.product else None,
                    "product_sku": item.product.sku if item.product else None,
                    "ordered_quantity": item.ordered_quantity,
                    "received_quantity": item.received_quantity,
                    "accepted_quantity": item.accepted_quantity,
                    "rejected_quantity": item.rejected_quantity,
                    "condition": item.condition,
                    "batch_number": item.batch_number,
                    "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                    "unit_price": float(item.unit_price),
                    "line_total": float(item.line_total),
                }
                for item in g.line_items
            ],
            "completed_at": g.completed_at.isoformat() if g.completed_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }

    async def create_grn(
        self,
        purchase_order_id: uuid.UUID,
        received_by_id: uuid.UUID,
        receipt_date: date,
        items: list[dict],
        supplier_invoice_number: str | None = None,
        supplier_invoice_date: date | None = None,
        notes: str | None = None,
        auto_complete: bool = True,
    ) -> dict:
        po = await self.po_repo.get_by_id(purchase_order_id)
        if not po:
            raise ResourceNotFoundException("PurchaseOrder", str(purchase_order_id))

        if po.status not in (POStatus.APPROVED, POStatus.PARTIALLY_RECEIVED):
            raise BusinessRuleViolationException(
                f"Cannot create GRN for PO in status '{po.status}'. Must be APPROVED or PARTIALLY_RECEIVED."
            )

        grn_number = await self.repo.generate_grn_number()
        initial_status = GRNStatus.COMPLETED if auto_complete else GRNStatus.DRAFT

        grn = await self.repo.create(
            grn_number=grn_number,
            purchase_order_id=po.id,
            warehouse_id=po.warehouse_id,
            received_by_id=received_by_id,
            status=initial_status,
            receipt_date=receipt_date,
            supplier_invoice_number=supplier_invoice_number,
            supplier_invoice_date=supplier_invoice_date,
            notes=notes,
            completed_at=datetime.now(timezone.utc) if auto_complete else None,
        )

        for item_data in items:
            product_id = uuid.UUID(str(item_data["product_id"]))
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                raise ResourceNotFoundException("Product", str(product_id))

            ordered_qty = int(item_data.get("ordered_quantity", 0))
            received_qty = int(item_data["received_quantity"])
            accepted_qty = int(item_data.get("accepted_quantity", received_qty))
            rejected_qty = received_qty - accepted_qty
            unit_price = Decimal(str(item_data.get("unit_price", product.cost_price)))
            line_total = Decimal(accepted_qty) * unit_price
            batch_num = item_data.get("batch_number")
            exp_date = item_data.get("expiry_date")

            await self.repo.add_line_item(
                grn_id=grn.id,
                product_id=product.id,
                po_line_item_id=uuid.UUID(str(item_data["po_line_item_id"])) if item_data.get("po_line_item_id") else None,
                ordered_quantity=ordered_qty,
                received_quantity=received_qty,
                accepted_quantity=accepted_qty,
                rejected_quantity=rejected_qty,
                condition=item_data.get("condition", StockCondition.GOOD),
                batch_number=batch_num,
                expiry_date=exp_date,
                unit_price=unit_price,
                line_total=line_total,
            )

            # If completing, update inventory and ledger
            if auto_complete and accepted_qty > 0:
                stock = await self.inv_repo.get_or_create_stock(product.id, po.warehouse_id)
                qty_before = stock.quantity_on_hand
                stock.quantity_on_hand += accepted_qty
                qty_after = stock.quantity_on_hand

                await self.inv_repo.record_transaction(
                    product_id=product.id,
                    warehouse_id=po.warehouse_id,
                    transaction_type=InventoryTransactionType.GRN_RECEIPT,
                    quantity_change=accepted_qty,
                    quantity_before=qty_before,
                    quantity_after=qty_after,
                    unit_cost=unit_price,
                    performed_by_id=received_by_id,
                    reference_type="grn",
                    reference_id=grn.id,
                    reason=f"Receipt via GRN {grn.grn_number}",
                )

                # If batch tracking
                if batch_num or exp_date:
                    batch = InventoryBatch(
                        product_id=product.id,
                        warehouse_id=po.warehouse_id,
                        grn_id=grn.id,
                        batch_number=batch_num,
                        expiry_date=exp_date,
                        quantity_received=accepted_qty,
                        quantity_remaining=accepted_qty,
                        unit_cost=unit_price,
                    )
                    self.db.add(batch)

        # Update PO status
        po.status = POStatus.FULLY_RECEIVED
        await self.db.flush()

        logger.info("Created and completed GRN %s for PO %s", grn.grn_number, po.po_number)
        return await self.get_grn(grn.id)
