"""
app/api/v1/alerts.py — Alerts System (Low Stock, Expiring, Dead Stock)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUserDep, DBDep
from app.core.response import success_response
from app.domain.models.inventory import InventoryBatch, InventoryStock, InventoryTransaction
from app.domain.models.product import Product
from app.domain.models.warehouse import Warehouse

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])


@router.get("/low-stock", summary="Get low stock alerts")
async def get_low_stock_alerts(
    db: DBDep,
    current_user: CurrentUserDep,
):
    """Returns products where current inventory on hand is <= reorder point."""
    result = await db.execute(
        select(Product, InventoryStock, Warehouse)
        .join(InventoryStock, InventoryStock.product_id == Product.id)
        .join(Warehouse, Warehouse.id == InventoryStock.warehouse_id)
        .where(InventoryStock.quantity_on_hand <= Product.reorder_point)
        .order_by(InventoryStock.quantity_on_hand.asc())
    )
    rows = result.all()
    alerts = []
    for prod, stock, wh in rows:
        deficit = max(0, prod.reorder_point - stock.quantity_on_hand)
        severity = "CRITICAL" if stock.quantity_on_hand <= prod.min_stock else "WARNING"
        alerts.append({
            "product_id": str(prod.id),
            "sku": prod.sku,
            "name": prod.name,
            "warehouse_id": str(wh.id),
            "warehouse_name": wh.name,
            "quantity_on_hand": stock.quantity_on_hand,
            "reorder_point": prod.reorder_point,
            "min_stock": prod.min_stock,
            "suggested_reorder_quantity": prod.reorder_quantity,
            "deficit": deficit,
            "severity": severity,
        })
    return success_response(data=alerts, message="Low stock alerts retrieved")


@router.get("/expiring", summary="Get expiring stock alerts")
async def get_expiring_alerts(
    db: DBDep,
    current_user: CurrentUserDep,
    days: int = Query(default=30, ge=1, le=180),
):
    """Returns inventory batches that expire within the next N days."""
    target_date = date.today() + timedelta(days=days)
    result = await db.execute(
        select(InventoryBatch, Product, Warehouse)
        .join(Product, Product.id == InventoryBatch.product_id)
        .join(Warehouse, Warehouse.id == InventoryBatch.warehouse_id)
        .where(
            InventoryBatch.expiry_date <= target_date,
            InventoryBatch.quantity_remaining > 0,
        )
        .order_by(InventoryBatch.expiry_date.asc())
    )
    rows = result.all()
    alerts = []
    for batch, prod, wh in rows:
        days_left = (batch.expiry_date - date.today()).days if batch.expiry_date else None
        severity = "CRITICAL" if (days_left is not None and days_left <= 7) else "WARNING"
        alerts.append({
            "batch_id": str(batch.id),
            "batch_number": batch.batch_number,
            "product_id": str(prod.id),
            "sku": prod.sku,
            "product_name": prod.name,
            "warehouse_id": str(wh.id),
            "warehouse_name": wh.name,
            "quantity_remaining": batch.quantity_remaining,
            "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
            "days_until_expiry": days_left,
            "severity": severity,
            "is_expired": days_left is not None and days_left <= 0,
        })
    return success_response(data=alerts, message="Expiring batch alerts retrieved")


@router.get("/dead-stock", summary="Get dead stock alerts (no movement in N days)")
async def get_dead_stock_alerts(
    db: DBDep,
    current_user: CurrentUserDep,
    days_inactive: int = Query(default=60, ge=15, le=365),
):
    """Returns products in stock that haven't had any inventory movement in N days."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)

    # Subquery: products with transactions after cutoff date
    active_prod_ids = (
        select(InventoryTransaction.product_id)
        .where(InventoryTransaction.created_at >= cutoff_date)
        .scalar_subquery()
    )

    result = await db.execute(
        select(Product, InventoryStock, Warehouse)
        .join(InventoryStock, InventoryStock.product_id == Product.id)
        .join(Warehouse, Warehouse.id == InventoryStock.warehouse_id)
        .where(
            InventoryStock.quantity_on_hand > 0,
            Product.id.not_in(active_prod_ids),
        )
        .order_by(InventoryStock.quantity_on_hand.desc())
    )
    rows = result.all()
    alerts = []
    for prod, stock, wh in rows:
        stuck_capital = float(stock.quantity_on_hand * prod.cost_price)
        alerts.append({
            "product_id": str(prod.id),
            "sku": prod.sku,
            "name": prod.name,
            "warehouse_name": wh.name,
            "quantity_on_hand": stock.quantity_on_hand,
            "cost_price": float(prod.cost_price),
            "tied_capital": stuck_capital,
            "days_inactive_threshold": days_inactive,
        })
    return success_response(data=alerts, message="Dead stock alerts retrieved")
