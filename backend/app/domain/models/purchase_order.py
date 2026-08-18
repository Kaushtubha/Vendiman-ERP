"""
app/domain/models/purchase_order.py — Purchase Order Models

Tables: purchase_orders, purchase_order_line_items

WHY PO number as human-readable (not UUID):
    POs are referenced in communication with suppliers and in printed documents.
    A readable PO number (PO-2024-001234) is essential for operations.
    The UUID `id` is used for internal lookups and foreign keys.

WHY PO total denormalized (not computed at query time):
    Summing line items on every PO query is expensive. The service layer
    updates the PO total whenever a line item is added/modified/deleted.
    Keeps the list endpoint O(1) per row.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import POLineItemStatus, POStatus


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # References
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=POStatus.DRAFT, index=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Financials (denormalized totals)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    # Docs
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="purchase_orders")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="purchase_orders")  # type: ignore[name-defined]
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])  # type: ignore[name-defined]
    approved_by: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by_id])  # type: ignore[name-defined]
    line_items: Mapped[list["PurchaseOrderLineItem"]] = relationship(
        "PurchaseOrderLineItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    grns: Mapped[list["GoodsReceiptNote"]] = relationship(  # type: ignore[name-defined]
        "GoodsReceiptNote", back_populates="purchase_order"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder po_number={self.po_number} status={self.status}>"


class PurchaseOrderLineItem(Base):
    __tablename__ = "purchase_order_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Quantities
    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=18)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default=POLineItemStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product", back_populates="po_line_items")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<POLineItem product_id={self.product_id} qty={self.ordered_quantity}>"
