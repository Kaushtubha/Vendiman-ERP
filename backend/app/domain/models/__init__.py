"""
app/domain/models/__init__.py

Exports all ORM models. Importing this package registers all models
with Base.metadata — required for Alembic autogenerate.

NOTE: `order.py` (CustomerOrder / OrderLineItem) is no longer imported
here — it modeled a quick-commerce delivery-order flow that doesn't apply
to unattended vending machines. The file is left in place (not deleted)
so nothing else in the tree breaks on import; it can be removed once
po_repository.py's stray references are cleaned up. Sales are now
represented by `VendTransaction` (transaction.py).
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
from app.domain.models.machine import Machine, MachineSlot
from app.domain.models.transaction import VendTransaction, ImportBatch
from app.domain.models.delivery_challan import DeliveryChallan, DCLineItem
from app.domain.models.machine_receipt import MachineReceipt, MachineReceiptLineItem

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
    "Machine",
    "MachineSlot",
    "VendTransaction",
    "ImportBatch",
    "DeliveryChallan",
    "DCLineItem",
    "MachineReceipt",
    "MachineReceiptLineItem",
]
