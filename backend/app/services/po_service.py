"""
app/services/po_service.py — Purchase Order Business Logic
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolationException, ResourceNotFoundException
from app.domain.enums import POLineItemStatus, POStatus
from app.repositories.po_repository import PurchaseOrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PurchaseOrderRepository(db)
        self.product_repo = ProductRepository(db)
        self.supplier_repo = SupplierRepository(db)

    async def list_pos(
        self,
        offset: int = 0,
        limit: int = 25,
        supplier_id: uuid.UUID | None = None,
        warehouse_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[dict], int]:
        pos, total = await self.repo.list_pos(
            offset=offset,
            limit=limit,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            status=status,
        )
        return [
            {
                "id": str(p.id),
                "po_number": p.po_number,
                "supplier_id": str(p.supplier_id),
                "supplier_name": p.supplier.name if p.supplier else None,
                "warehouse_id": str(p.warehouse_id),
                "warehouse_name": p.warehouse.name if p.warehouse else None,
                "status": p.status,
                "order_date": p.order_date.isoformat() if p.order_date else None,
                "expected_delivery_date": p.expected_delivery_date.isoformat() if p.expected_delivery_date else None,
                "total_amount": float(p.total_amount),
                "subtotal": float(p.subtotal),
                "tax_amount": float(p.tax_amount),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pos
        ], total

    async def get_po(self, po_id: uuid.UUID) -> dict:
        p = await self.repo.get_by_id(po_id)
        if not p:
            raise ResourceNotFoundException("PurchaseOrder", str(po_id))
        return {
            "id": str(p.id),
            "po_number": p.po_number,
            "supplier_id": str(p.supplier_id),
            "supplier_name": p.supplier.name if p.supplier else None,
            "supplier_code": p.supplier.code if p.supplier else None,
            "warehouse_id": str(p.warehouse_id),
            "warehouse_name": p.warehouse.name if p.warehouse else None,
            "status": p.status,
            "order_date": p.order_date.isoformat() if p.order_date else None,
            "expected_delivery_date": p.expected_delivery_date.isoformat() if p.expected_delivery_date else None,
            "subtotal": float(p.subtotal),
            "tax_amount": float(p.tax_amount),
            "discount_amount": float(p.discount_amount),
            "total_amount": float(p.total_amount),
            "notes": p.notes,
            "line_items": [
                {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": item.product.name if item.product else None,
                    "product_sku": item.product.sku if item.product else None,
                    "ordered_quantity": item.ordered_quantity,
                    "received_quantity": item.received_quantity,
                    "unit_price": float(item.unit_price),
                    "gst_rate": float(item.gst_rate),
                    "tax_amount": float(item.tax_amount),
                    "line_total": float(item.line_total),
                    "status": item.status,
                }
                for item in p.line_items
            ],
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    async def create_po(
        self,
        supplier_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        created_by_id: uuid.UUID,
        order_date: date,
        items: list[dict],
        expected_delivery_date: date | None = None,
        notes: str | None = None,
    ) -> dict:
        supplier = await self.supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise ResourceNotFoundException("Supplier", str(supplier_id))

        po_number = await self.repo.generate_po_number()

        # Calculate totals
        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")

        po = await self.repo.create(
            po_number=po_number,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            created_by_id=created_by_id,
            status=POStatus.DRAFT,
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            notes=notes,
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )

        for item_data in items:
            product = await self.product_repo.get_by_id(uuid.UUID(str(item_data["product_id"])))
            if not product:
                raise ResourceNotFoundException("Product", str(item_data["product_id"]))

            qty = int(item_data["ordered_quantity"])
            unit_price = Decimal(str(item_data.get("unit_price", product.cost_price)))
            gst_rate = Decimal(str(product.gst_rate if hasattr(product, "gst_rate") else 18))
            
            line_subtotal = Decimal(qty) * unit_price
            line_tax = (line_subtotal * gst_rate) / Decimal("100")
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            total_tax += line_tax

            await self.repo.add_line_item(
                purchase_order_id=po.id,
                product_id=product.id,
                ordered_quantity=qty,
                received_quantity=0,
                unit_price=unit_price,
                gst_rate=gst_rate,
                tax_amount=line_tax,
                line_total=line_total,
                status=POLineItemStatus.PENDING,
            )

        po.subtotal = subtotal
        po.tax_amount = total_tax
        po.total_amount = subtotal + total_tax
        await self.db.flush()

        logger.info("Created PO %s with %d items total=%.2f", po.po_number, len(items), po.total_amount)
        return await self.get_po(po.id)

    async def approve_po(self, po_id: uuid.UUID, approved_by_id: uuid.UUID) -> dict:
        po = await self.repo.get_by_id(po_id)
        if not po:
            raise ResourceNotFoundException("PurchaseOrder", str(po_id))
        if po.status not in (POStatus.DRAFT, POStatus.PENDING_APPROVAL):
            raise BusinessRuleViolationException(f"Cannot approve PO in status '{po.status}'")

        await self.repo.update_status(
            po_id,
            status=POStatus.APPROVED,
            approved_by_id=approved_by_id,
            approved_at=datetime.now(timezone.utc),
        )
        return await self.get_po(po_id)
