"""
app/api/v1/inventory.py — Inventory Management API
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, DBDep, PaginationDep
from app.core.response import paginated_response, success_response
from app.domain.enums import InventoryAdjustmentReason
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class StockAdjustRequest(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    new_quantity: int = Field(ge=0)
    reason: str = Field(default="physical_count")
    notes: str | None = None


@router.get("", summary="List current stock levels")
async def list_stocks(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    warehouse_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
):
    service = InventoryService(db)
    items, total = await service.list_stocks(
        offset=pagination.offset,
        limit=pagination.limit,
        warehouse_id=warehouse_id,
        search=search,
        low_stock_only=low_stock_only,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="Stock levels retrieved",
    )


@router.post("/adjust", summary="Manual stock adjustment (updates ledger)")
async def adjust_stock(
    body: StockAdjustRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    user_id = uuid.UUID(current_user["sub"]) if "sub" in current_user else None
    service = InventoryService(db)
    result = await service.adjust_stock(
        product_id=body.product_id,
        warehouse_id=body.warehouse_id,
        new_quantity=body.new_quantity,
        reason=body.reason,
        performed_by_id=user_id,
        notes=body.notes,
    )
    return success_response(data=result, message="Stock adjusted successfully")


@router.get("/transactions", summary="List immutable inventory transactions ledger")
async def list_transactions(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    product_id: uuid.UUID | None = Query(default=None),
    warehouse_id: uuid.UUID | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
):
    service = InventoryService(db)
    items, total = await service.list_transactions(
        offset=pagination.offset,
        limit=pagination.limit,
        product_id=product_id,
        warehouse_id=warehouse_id,
        transaction_type=transaction_type,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="Inventory ledger retrieved",
    )


@router.get("/expiring", summary="List products expiring soon")
async def list_expiring_stock(
    db: DBDep,
    current_user: CurrentUserDep,
    days: int = Query(default=30, ge=1, le=365),
):
    service = InventoryService(db)
    items = await service.get_expiring_stock(days_threshold=days)
    return success_response(data=items, message="Expiring batches retrieved")
