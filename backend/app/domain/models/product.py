"""
app/domain/models/product.py — Product & Category Models

Tables: product_categories, products

WHY SKU + barcode both indexed:
    SKU is internal identifier used in POs, GRNs, reports.
    Barcode is the scanner-readable code (EAN-13, UPC-A).
    Both need O(1) lookup — hence separate indexes.

WHY Numeric for prices/GST (not Float):
    Float arithmetic is approximate. Financial calculations with floats
    accumulate rounding errors. NUMERIC(10,2) is exact — standard for
    any monetary value in database systems.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import GSTRate, ProductStatus


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<ProductCategory name={self.name}>"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="piece")  # piece, kg, litre, etc.

    # Pricing
    mrp: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)            # Max retail price
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)     # Purchase cost
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Our selling price

    # GST
    gst_rate: Mapped[str] = mapped_column(String(10), nullable=False, default=GSTRate.EIGHTEEN)
    hsn_code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HSN/SAC code for GST

    # Status & flags
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ProductStatus.ACTIVE)
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # For perishables

    # Stock thresholds
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    min_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Media
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Slot-space efficiency (Vendiman Module 4) — the physical space one unit
    # occupies in a machine spiral/tray. Defaults to 1 so profit-per-slot
    # gracefully degrades to plain profit-per-unit until real values are set.
    slot_space_units: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    category: Mapped["ProductCategory | None"] = relationship("ProductCategory", back_populates="products")
    inventory_stocks: Mapped[list["InventoryStock"]] = relationship(  # type: ignore[name-defined]
        "InventoryStock", back_populates="product"
    )
    inventory_batches: Mapped[list["InventoryBatch"]] = relationship(  # type: ignore[name-defined]
        "InventoryBatch", back_populates="product"
    )
    po_line_items: Mapped[list["PurchaseOrderLineItem"]] = relationship(  # type: ignore[name-defined]
        "PurchaseOrderLineItem", back_populates="product"
    )
    grn_line_items: Mapped[list["GRNLineItem"]] = relationship(  # type: ignore[name-defined]
        "GRNLineItem", back_populates="product"
    )
    # NOTE: the old `order_line_items` relationship (to OrderLineItem) was
    # removed — that model belonged to the deprecated customer-order flow.
    # Sales are now on VendTransaction, referenced by product_id without a
    # back_populates collection here (no need to load "all transactions
    # for a product" through the Product object; queries go through the
    # vend_transactions table directly, indexed on product_id).

    vend_transactions: Mapped[list["VendTransaction"]] = relationship(  # type: ignore[name-defined]
        "VendTransaction", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product sku={self.sku} name={self.name}>"
