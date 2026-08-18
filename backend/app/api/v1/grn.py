"""
app/api/v1/grn.py — Goods Receipt Notes (DGRN) API
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
from app.domain.enums import StockCondition
from app.services.grn_service import GRNService

router = APIRouter(prefix="/grn", tags=["Goods Receipt Note"])


class GRNLineItemCreate(BaseModel):
    product_id: uuid.UUID
    po_line_item_id: uuid.UUID | None = None
    ordered_quantity: int = 0
    received_quantity: int = Field(ge=1)
    accepted_quantity: int | None = None
    condition: StockCondition = StockCondition.GOOD
    batch_number: str | None = None
    expiry_date: date | None = None
    unit_price: Decimal | None = None


class GRNCreateRequest(BaseModel):
    purchase_order_id: uuid.UUID
    receipt_date: date = Field(default_factory=date.today)
    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    notes: str | None = None
    items: list[GRNLineItemCreate] = Field(min_length=1)
    auto_complete: bool = True


@router.get("", summary="List GRNs (Goods Receipt Notes)")
async def list_grns(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    warehouse_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
):
    service = GRNService(db)
    items, total = await service.list_grns(
        offset=pagination.offset,
        limit=pagination.limit,
        warehouse_id=warehouse_id,
        status=status,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="GRNs retrieved successfully",
    )


@router.post("", summary="Create & process GRN against Purchase Order", status_code=status.HTTP_201_CREATED)
async def create_grn(
    body: GRNCreateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    user_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else uuid.uuid4()
    service = GRNService(db)
    result = await service.create_grn(
        purchase_order_id=body.purchase_order_id,
        received_by_id=user_id,
        receipt_date=body.receipt_date,
        items=[item.model_dump() for item in body.items],
        supplier_invoice_number=body.supplier_invoice_number,
        supplier_invoice_date=body.supplier_invoice_date,
        notes=body.notes,
        auto_complete=body.auto_complete,
    )
    return created_response(data=result, message="GRN processed and inventory updated")


@router.get("/{grn_id}", summary="Get GRN details")
async def get_grn(
    grn_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = GRNService(db)
    result = await service.get_grn(grn_id)
    return success_response(data=result, message="GRN details retrieved")
