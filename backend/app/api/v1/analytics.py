"""
app/api/v1/analytics.py — Analytics & Profitability API

Provides endpoints for:
    - Overview KPIs (Total Products, Total Stock Value, Monthly PO Spend, Low Stock Count)
    - Profitability per Product / Slot
    - Stock distribution by category
    - Daily movement trends
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUserDep, DBDep
from app.core.response import success_response
from app.domain.models.inventory import InventoryBatch, InventoryStock, InventoryTransaction
from app.domain.models.product import Product, ProductCategory
from app.domain.models.purchase_order import PurchaseOrder
from app.domain.models.supplier import Supplier

router = APIRouter(prefix="/analytics", tags=["Analytics & KPIs"])


@router.get("/kpis", summary="Dashboard KPI metrics")
async def get_kpi_summary(
    db: DBDep,
    current_user: CurrentUserDep,
):
    # Total Active Products
    prod_count_res = await db.execute(select(func.count(Product.id)))
    total_products = prod_count_res.scalar_one()

    # Total Suppliers
    supp_count_res = await db.execute(select(func.count(Supplier.id)))
    total_suppliers = supp_count_res.scalar_one()

    # Total Stock Value (on hand * cost price)
    stock_val_res = await db.execute(
        select(func.coalesce(func.sum(InventoryStock.quantity_on_hand * Product.cost_price), 0))
        .join(Product, Product.id == InventoryStock.product_id)
    )
    total_stock_value = float(stock_val_res.scalar_one())

    # Total Retail Value (on hand * mrp)
    retail_val_res = await db.execute(
        select(func.coalesce(func.sum(InventoryStock.quantity_on_hand * Product.mrp), 0))
        .join(Product, Product.id == InventoryStock.product_id)
    )
    total_retail_value = float(retail_val_res.scalar_one())

    # Low Stock Items Count
    low_stock_res = await db.execute(
        select(func.count(InventoryStock.id))
        .join(Product, Product.id == InventoryStock.product_id)
        .where(InventoryStock.quantity_on_hand <= Product.reorder_point)
    )
    low_stock_count = low_stock_res.scalar_one()

    # Total POs
    po_count_res = await db.execute(select(func.count(PurchaseOrder.id)))
    total_pos = po_count_res.scalar_one()

    return success_response(
        data={
            "total_products": total_products,
            "total_suppliers": total_suppliers,
            "total_stock_value": total_stock_value,
            "total_retail_value": total_retail_value,
            "potential_profit": round(total_retail_value - total_stock_value, 2),
            "low_stock_count": low_stock_count,
            "total_purchase_orders": total_pos,
        },
        message="KPI summary retrieved",
    )


@router.get("/profit-per-slot", summary="Profitability analysis by product/slot")
async def get_profit_per_slot(
    db: DBDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Calculates profit margins per product slot.
    Margin = Selling Price - Cost Price
    Margin % = (Margin / Selling Price) * 100
    """
    result = await db.execute(
        select(Product, InventoryStock.quantity_on_hand)
        .outerjoin(InventoryStock, InventoryStock.product_id == Product.id)
        .order_by(Product.name)
        .limit(limit)
    )
    rows = result.all()
    slots = []
    for prod, on_hand in rows:
        mrp = float(prod.mrp)
        cost = float(prod.cost_price)
        selling = float(prod.selling_price)
        unit_profit = round(selling - cost, 2)
        margin_percent = round((unit_profit / selling * 100) if selling > 0 else 0, 1)
        potential_slot_profit = round(unit_profit * (on_hand or 0), 2)

        slots.append({
            "product_id": str(prod.id),
            "sku": prod.sku,
            "name": prod.name,
            "brand": prod.brand,
            "mrp": mrp,
            "cost_price": cost,
            "selling_price": selling,
            "unit_profit": unit_profit,
            "margin_percent": margin_percent,
            "stock_on_hand": on_hand or 0,
            "potential_total_profit": potential_slot_profit,
        })

    return success_response(data=slots, message="Profit per slot retrieved")


@router.get("/category-distribution", summary="Stock breakdown by category")
async def get_category_distribution(
    db: DBDep,
    current_user: CurrentUserDep,
):
    result = await db.execute(
        select(
            ProductCategory.name,
            func.count(Product.id).label("product_count"),
            func.coalesce(func.sum(InventoryStock.quantity_on_hand), 0).label("total_units"),
        )
        .outerjoin(Product, Product.category_id == ProductCategory.id)
        .outerjoin(InventoryStock, InventoryStock.product_id == Product.id)
        .group_by(ProductCategory.id, ProductCategory.name)
    )
    rows = result.all()
    data = [
        {
            "category": row[0],
            "product_count": row[1],
            "total_units": int(row[2]),
        }
        for row in rows
    ]
    return success_response(data=data, message="Category distribution retrieved")
