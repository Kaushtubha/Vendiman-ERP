"""
app/domain/models/supplier.py — Supplier Model

Table: suppliers

Suppliers are the vendors from whom we raise Purchase Orders.
Tracks GST registration, bank details, performance rating, and contact info.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import SupplierRating, SupplierStatus


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    # Contact
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alternate_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Address
    address_line1: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_line2: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")

    # GST & Tax
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)
    pan_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Bank details for payments
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Performance
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SupplierStatus.ACTIVE)
    rating: Mapped[str] = mapped_column(String(50), nullable=False, default=SupplierRating.GOOD)
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # Stats (denormalized for speed — updated by service layer)
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_spend: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    on_time_delivery_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(  # type: ignore[name-defined]
        "PurchaseOrder", back_populates="supplier"
    )

    def __repr__(self) -> str:
        return f"<Supplier code={self.code} name={self.name}>"
