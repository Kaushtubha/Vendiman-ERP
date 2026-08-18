"""
app/domain/models/grn.py — Goods Receipt Note Models

Tables: goods_receipt_notes, grn_line_items

GRN is the physical receipt of goods against a Purchase Order.
Key business rules enforced at service level (not model level):
    - Cannot create GRN for a DRAFT or CANCELLED PO
    - Received quantity cannot exceed ordered quantity
    - GRN completion updates inventory_stocks automatically
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
from app.domain.enums import GRNStatus, StockCondition


class GoodsReceiptNote(Base):
    __tablename__ = "goods_receipt_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    received_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default=GRNStatus.DRAFT, index=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Supplier invoice details
    supplier_invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    discrepancy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="grns")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="grns")  # type: ignore[name-defined]
    received_by: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    line_items: Mapped[list["GRNLineItem"]] = relationship(
        "GRNLineItem",
        back_populates="grn",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GRN grn_number={self.grn_number} status={self.status}>"


class GRNLineItem(Base):
    __tablename__ = "grn_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goods_receipt_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    po_line_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Quantities
    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Condition & Batch
    condition: Mapped[str] = mapped_column(String(50), nullable=False, default=StockCondition.GOOD)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Pricing (may differ from PO price if invoice differs)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    grn: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product", back_populates="grn_line_items")  # type: ignore[name-defined]
