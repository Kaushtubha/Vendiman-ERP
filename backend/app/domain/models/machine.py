"""
app/domain/models/machine.py — Vending Machine & Physical Slot Models

Tables: machines, machine_slots

WHY machines is its own table (not folded into warehouses):
    A vending machine is a physical, unattended selling point — it has a
    location, a client/host site, a hardware UID, and a fixed set of
    physical slots (BinNumber/OPCode). It is the "destination" for stock
    dispatched from the warehouse, and the source of every sales
    transaction. Modeling it separately from `warehouses` keeps the
    supplier→warehouse and warehouse→machine flows independent, which
    matches how the business actually operates (DGRN Module 2).

WHY machine_slots is its own table (not a JSON column on machines):
    Slot occupancy changes on every sale and every restock — it needs
    row-level updates and indexing on product_id (for the slot-space
    profitability ranking in Module 4). A JSON blob would require
    read-modify-write of the whole machine row on every vend.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import MachineStatus


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identity — from the sales export (MachineId, MachineUID, MachineName)
    source_machine_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    machine_uid: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hardware
    telemetry_serial_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terminal_serial_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Location / hosting client (OperationLocationName, Client Id/Name, Client Location Name)
    operation_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    client_source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Sourcing warehouse — where restock dispatches originate from
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False, default=MachineStatus.ACTIVE, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    warehouse: Mapped["Warehouse | None"] = relationship("Warehouse")  # type: ignore[name-defined]
    slots: Mapped[list["MachineSlot"]] = relationship(
        "MachineSlot", back_populates="machine", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Machine uid={self.machine_uid} name={self.name}>"


class MachineSlot(Base):
    """
    A physical bin/spiral position inside a machine (BinNumber/OPCode in the
    source export). Tracks which product currently occupies it, its live
    quantity, and its physical capacity — the inputs to the slot-space
    profitability metric (profit per slot occupied).
    """

    __tablename__ = "machine_slots"
    __table_args__ = (UniqueConstraint("machine_id", "bin_number", name="uq_machine_slot_bin"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bin_number: Mapped[str] = mapped_column(String(20), nullable=False)
    op_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    slot_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # max units the slot holds
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    machine: Mapped["Machine"] = relationship("Machine", back_populates="slots")
    product: Mapped["Product | None"] = relationship("Product")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<MachineSlot machine_id={self.machine_id} bin={self.bin_number}>"
