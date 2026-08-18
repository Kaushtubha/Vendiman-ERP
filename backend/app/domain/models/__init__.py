"""
app/domain/models/__init__.py

Exports all ORM models. Importing this package registers all models
with Base.metadata — required for Alembic autogenerate.
"""

from app.domain.models.user import User, RefreshToken
from app.domain.models.product import Product, ProductCategory
from app.domain.models.supplier import Supplier
from app.domain.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from app.domain.models.grn import GoodsReceiptNote, GRNLineItem
from app.domain.models.inventory import (
    InventoryStock,
    InventoryTransaction,
    InventoryBatch,
)
from app.domain.models.warehouse import Warehouse, WarehouseTransfer, TransferLineItem
from app.domain.models.order import CustomerOrder, OrderLineItem
from app.domain.models.delivery_challan import DeliveryChallan, DCLineItem

__all__ = [
    "User",
    "RefreshToken",
    "Product",
    "ProductCategory",
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderLineItem",
    "GoodsReceiptNote",
    "GRNLineItem",
    "InventoryStock",
    "InventoryTransaction",
    "InventoryBatch",
    "Warehouse",
    "WarehouseTransfer",
    "TransferLineItem",
    "CustomerOrder",
    "OrderLineItem",
    "DeliveryChallan",
    "DCLineItem",
]
