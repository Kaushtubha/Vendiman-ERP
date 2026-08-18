"""
app/domain/models/order.py — Customer Order Models

Tables: customer_orders, order_line_items

Simulates a quick-commerce order with a 60-second stock reservation window.
State machine: CREATED → STOCK_RESERVED → PAYMENT_PENDING → PAYMENT_CONFIRMED
               → DISPATCHED → DELIVERED
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
from app.domain.enums import OrderStatus, PaymentMethod, PaymentStatus


class CustomerOrder(Base):
    __tablename__ = "customer_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Customer info (simplified — no separate customers table for this ERP)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=OrderStatus.CREATED, index=True)
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False, default=PaymentStatus.PENDING)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Financials
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    delivery_charge: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Reservation TTL (for the 60-second reservation window)
    reservation_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # type: ignore[name-defined]
    line_items: Mapped[list["OrderLineItem"]] = relationship(
        "OrderLineItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    delivery_challan: Mapped["DeliveryChallan | None"] = relationship(  # type: ignore[name-defined]
        "DeliveryChallan", back_populates="order", uselist=False
    )

    def __repr__(self) -> str:
        return f"<CustomerOrder number={self.order_number} status={self.status}>"


class OrderLineItem(Base):
    __tablename__ = "order_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_orders.id", ondelete="CASCADE"),
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
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["CustomerOrder"] = relationship("CustomerOrder", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_line_items")  # type: ignore[name-defined]
