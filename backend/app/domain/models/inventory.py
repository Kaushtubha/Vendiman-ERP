"""
app/domain/models/inventory.py — Inventory Models

Tables: inventory_stocks, inventory_transactions, inventory_batches

DESIGN:
    inventory_stocks — one row per (product, warehouse). Tracks current levels.
    inventory_transactions — immutable ledger of every stock movement.
    inventory_batches — per-batch tracking for perishables (expiry, batch#).

WHY separate stock and transaction tables:
    The stocks table is the "balance sheet" — current state, fast lookup.
    The transactions table is the "ledger" — immutable audit trail.
    Both are needed:
    - Operations query stocks (O(1) per product/warehouse pair)
    - Auditors and reports query transactions (time-range queries)

WHY inventory_transactions is IMMUTABLE:
    Never UPDATE or DELETE inventory transactions. Only INSERT.
    This gives a complete, trustworthy audit trail.
    Corrections are done by inserting a counter-entry (like accounting).
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
from app.domain.enums import InventoryAdjustmentReason, InventoryTransactionType, StockCondition


class InventoryStock(Base):
    """
    Current stock level for a (product, warehouse) pair.
    This is the denormalized "balance" — updated on every stock movement.

    WHY available_quantity = quantity_on_hand - quantity_reserved:
        When a customer places an order, stock is "reserved" instantly.
        Available quantity decreases but physical stock hasn't moved yet.
        This prevents overselling under concurrent order load.
    """

    __tablename__ = "inventory_stocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_damaged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Costing — weighted average cost price
    average_cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_stocks")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_stocks")  # type: ignore[name-defined]

    @property
    def available_quantity(self) -> int:
        """Stock that can actually be sold or transferred."""
        return max(0, self.quantity_on_hand - self.quantity_reserved)

    def __repr__(self) -> str:
        return (
            f"<InventoryStock product_id={self.product_id} "
            f"warehouse_id={self.warehouse_id} on_hand={self.quantity_on_hand}>"
        )


class InventoryTransaction(Base):
    """
    Immutable ledger of every stock movement.
    Never updated or deleted after creation.
    """

    __tablename__ = "inventory_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    performed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(60), nullable=False, index=True
    )
    quantity_change: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Positive = stock IN, negative = stock OUT",
    )
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Reference to the source document
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # grn, order, transfer, etc.
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,  # Time-range queries on the ledger
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # type: ignore[name-defined]
    performed_by: Mapped["User | None"] = relationship("User")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<InventoryTransaction type={self.transaction_type} "
            f"qty_change={self.quantity_change}>"
        )


class InventoryBatch(Base):
    """
    Per-batch tracking for perishable products.
    Each GRN receipt creates a batch entry with expiry date.
    Stock depletion reduces quantity_remaining.
    """

    __tablename__ = "inventory_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    grn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("goods_receipt_notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False, default=StockCondition.GOOD)

    unit_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_batches")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<InventoryBatch batch={self.batch_number} expiry={self.expiry_date} qty={self.quantity_remaining}>"
