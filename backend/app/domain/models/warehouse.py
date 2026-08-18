"""
app/domain/models/warehouse.py — Warehouse & Transfer Models

Tables: warehouses, warehouse_transfers, transfer_line_items

WHY warehouse model before GRN/Inventory:
    GRNs and Inventory both reference warehouse_id as FK.
    The warehouse model must be created first (FK constraint).
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
from app.domain.enums import TransferStatus, WarehouseStatus, WarehouseType


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default=WarehouseType.DARK_STORE)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=WarehouseStatus.ACTIVE)

    # Address
    address_line1: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Capacity
    total_capacity_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    manager: Mapped["User | None"] = relationship("User", foreign_keys=[manager_id])  # type: ignore[name-defined]
    inventory_stocks: Mapped[list["InventoryStock"]] = relationship(  # type: ignore[name-defined]
        "InventoryStock", back_populates="warehouse"
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(  # type: ignore[name-defined]
        "PurchaseOrder", back_populates="warehouse"
    )
    grns: Mapped[list["GoodsReceiptNote"]] = relationship(  # type: ignore[name-defined]
        "GoodsReceiptNote", back_populates="warehouse"
    )
    outbound_transfers: Mapped[list["WarehouseTransfer"]] = relationship(
        "WarehouseTransfer",
        foreign_keys="[WarehouseTransfer.from_warehouse_id]",
        back_populates="from_warehouse",
    )
    inbound_transfers: Mapped[list["WarehouseTransfer"]] = relationship(
        "WarehouseTransfer",
        foreign_keys="[WarehouseTransfer.to_warehouse_id]",
        back_populates="to_warehouse",
    )

    def __repr__(self) -> str:
        return f"<Warehouse code={self.code} type={self.type}>"


class WarehouseTransfer(Base):
    __tablename__ = "warehouse_transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    from_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    to_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default=TransferStatus.REQUESTED)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    from_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", foreign_keys=[from_warehouse_id], back_populates="outbound_transfers"
    )
    to_warehouse: Mapped["Warehouse"] = relationship(
        "Warehouse", foreign_keys=[to_warehouse_id], back_populates="inbound_transfers"
    )
    requested_by: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    line_items: Mapped[list["TransferLineItem"]] = relationship(
        "TransferLineItem",
        back_populates="transfer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<WarehouseTransfer number={self.transfer_number} status={self.status}>"


class TransferLineItem(Base):
    __tablename__ = "transfer_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouse_transfers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    dispatched_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    transfer: Mapped["WarehouseTransfer"] = relationship("WarehouseTransfer", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]
