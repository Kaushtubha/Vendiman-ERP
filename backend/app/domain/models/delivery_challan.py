"""
app/domain/models/delivery_challan.py — Delivery Challan Models

Tables: delivery_challans, dc_line_items

A Delivery Challan (DC) is generated when dispatching goods from a customer order.
It serves as a legal document in India for movement of goods.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import DCStatus


class DeliveryChallan(Base):
    __tablename__ = "delivery_challans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dc_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_orders.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # One DC per order
        index=True,
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DCStatus.GENERATED, index=True)

    # Delivery info
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    driver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vehicle_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Financials
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="delivery_challan")  # type: ignore[name-defined]
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # type: ignore[name-defined]
    created_by: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    line_items: Mapped[list["DCLineItem"]] = relationship(
        "DCLineItem",
        back_populates="delivery_challan",
        cascade="all, delete-orphan",
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

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    delivery_challan: Mapped["DeliveryChallan"] = relationship("DeliveryChallan", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]
