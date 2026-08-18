"""
app/api/v1/purchase_orders.py — Purchase Orders API
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, DBDep, PaginationDep
from app.core.response import created_response, paginated_response, success_response
from app.services.po_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


class POLineItemCreate(BaseModel):
    product_id: uuid.UUID
    ordered_quantity: int = Field(ge=1)
    unit_price: Decimal | None = None


class POCreateRequest(BaseModel):
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    order_date: date = Field(default_factory=date.today)
    expected_delivery_date: date | None = None
    items: list[POLineItemCreate] = Field(min_length=1)
    notes: str | None = None


@router.get("", summary="List purchase orders")
async def list_pos(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    supplier_id: uuid.UUID | None = Query(default=None),
    warehouse_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
):
    service = PurchaseOrderService(db)
    items, total = await service.list_pos(
        offset=pagination.offset,
        limit=pagination.limit,
        supplier_id=supplier_id,
        warehouse_id=warehouse_id,
        status=status,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="Purchase orders retrieved",
    )


@router.post("", summary="Create a new purchase order", status_code=status.HTTP_201_CREATED)
async def create_po(
    body: POCreateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    user_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else uuid.uuid4()
    service = PurchaseOrderService(db)
    result = await service.create_po(
        supplier_id=body.supplier_id,
        warehouse_id=body.warehouse_id,
        created_by_id=user_id,
        order_date=body.order_date,
        items=[item.model_dump() for item in body.items],
        expected_delivery_date=body.expected_delivery_date,
        notes=body.notes,
    )
    return created_response(data=result, message="Purchase order created")


@router.get("/{po_id}", summary="Get purchase order details")
async def get_po(
    po_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = PurchaseOrderService(db)
    result = await service.get_po(po_id)
    return success_response(data=result, message="Purchase order retrieved")


@router.post("/{po_id}/approve", summary="Approve purchase order")
async def approve_po(
    po_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUserDep,
):
    user_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else uuid.uuid4()
    service = PurchaseOrderService(db)
    result = await service.approve_po(po_id, approved_by_id=user_id)
    return success_response(data=result, message="Purchase order approved")
