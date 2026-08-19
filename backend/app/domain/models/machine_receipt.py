"""
app/domain/models/machine_receipt.py — Machine-side Goods Receipt

Tables: machine_receipts, machine_receipt_line_items

Confirms receipt of a DeliveryChallan at the machine end (Vendiman spec
Module 2, DGRN). Mirrors the GRN pattern used for supplier→warehouse
receipts (see grn.py), but scoped to warehouse→machine restocks:
    - Captures actual received qty vs dispatched qty per line
    - Flags condition and discrepancy per line
    - On completion, the service layer updates machine_slots.current_quantity,
      creates/updates the relevant batch (FIFO expiry), and writes an
      InventoryTransaction ledger entry with machine_id set.

WHY a separate table from GoodsReceiptNote (not the same table reused):
    GoodsReceiptNote is tightly coupled to a purchase_order_id (a supplier
    receipt always closes out a PO line). A machine restock closes out a
    DeliveryChallan line instead, and has no supplier/invoice fields.
    Forcing both flows into one table means every column becomes nullable
    and every query needs to branch on "which kind of receipt is this" —
    a dedicated table keeps both flows simple and their FKs mandatory.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import MachineDeliveryStatus, StockCondition


class MachineReceipt(Base):
    __tablename__ = "machine_receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    delivery_challan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_challans.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # one receipt per DC
        index=True,
    )
    machine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    received_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=MachineDeliveryStatus.PENDING, index=True
    )
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discrepancy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    delivery_challan: Mapped["DeliveryChallan"] = relationship(  # type: ignore[name-defined]
        "DeliveryChallan", back_populates="machine_receipt"
    )
    machine: Mapped["Machine"] = relationship("Machine")  # type: ignore[name-defined]
    received_by: Mapped["User | None"] = relationship("User")  # type: ignore[name-defined]
    line_items: Mapped[list["MachineReceiptLineItem"]] = relationship(
        "MachineReceiptLineItem",
        back_populates="machine_receipt",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MachineReceipt receipt_number={self.receipt_number} status={self.status}>"


class MachineReceiptLineItem(Base):
    __tablename__ = "machine_receipt_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machine_receipts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dc_line_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dc_line_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    dispatched_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    discrepancy_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    condition: Mapped[str] = mapped_column(String(50), nullable=False, default=StockCondition.GOOD)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    machine_receipt: Mapped["MachineReceipt"] = relationship("MachineReceipt", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]
