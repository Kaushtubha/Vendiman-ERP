"""
app/domain/models/delivery_challan.py — Delivery Challan Models (Warehouse → Machine)

Tables: delivery_challans, dc_line_items

A Delivery Challan (DC) is generated whenever stock is dispatched from the
warehouse to restock a vending machine (Vendiman spec Module 2, DGRN).
It is a legal document in India for movement of goods, and its
counterpart on the machine side is a MachineReceipt (see machine_receipt.py)
— together they form the DC → GRN restock workflow with status
Pending / Received / Discrepancy.

NOTE: previously this model was tied to `customer_orders` (a delivery-order
flow that doesn't apply to unattended vending machines). It now targets a
`machine_id` directly — a DC is simply "N units of product X, dispatched
from warehouse W, headed to machine M".
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import MachineDeliveryStatus


class DeliveryChallan(Base):
    __tablename__ = "delivery_challans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dc_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    machine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machines.id", ondelete="RESTRICT"),
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

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=MachineDeliveryStatus.PENDING, index=True
    )

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    machine: Mapped["Machine"] = relationship("Machine")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # type: ignore[name-defined]
    created_by: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    line_items: Mapped[list["DCLineItem"]] = relationship(
        "DCLineItem",
        back_populates="delivery_challan",
        cascade="all, delete-orphan",
    )
    machine_receipt: Mapped["MachineReceipt | None"] = relationship(  # type: ignore[name-defined]
        "MachineReceipt", back_populates="delivery_challan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<DeliveryChallan dc_number={self.dc_number} status={self.status}>"


class DCLineItem(Base):
    __tablename__ = "dc_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_challan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_challans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dispatched_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    delivery_challan: Mapped["DeliveryChallan"] = relationship("DeliveryChallan", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]
