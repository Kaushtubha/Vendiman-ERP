"""
app/domain/models/transaction.py — Vend Transaction Model

Table: vend_transactions

Replaces the old customer_orders / order_line_items pair (which modeled a
quick-commerce delivery order and doesn't apply to unattended vending
machines). Each row here is ONE order/vend attempt from the machine
telemetry export — this is a flat, append-only fact table, not a
normalized order+line-item pair, because the source data itself is one
row per (order, single item): a vend either succeeds or fails as a unit.

WHY denormalized / append-only (no separate "order" header table):
    The source export (section 3 of the spec) is one row per order, and
    in practice each order is for a single item/bin. Splitting into an
    orders header + line items table would require inventing a grouping
    key that isn't reliably present, and buys nothing — every query the
    app needs (sales by machine/product/date, best/worst sellers,
    failed-vend rate) is a straight aggregate over this table.

WHY both product_id (FK) and raw_item_name (text) are kept:
    product_id is null-able because the Excel importer does fuzzy/cleaned
    name matching against the product master (Item Name with the trailing
    "- Rs.NN" price stripped) — a small percentage of rows may fail to
    match on any given import (new SKU not yet in the product master,
    OCR/typo in the export). raw_item_name preserves the original text so
    those rows can be reconciled later instead of silently dropped.

INDEXES:
    machine_id + txn_date, product_id + txn_date, and txn_date alone are
    indexed per the spec's requirement to avoid full-table scans at
    100k+ rows/month volume.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.domain.enums import VendPaymentStatus, VendRefundStatus, VendStatus


class VendTransaction(Base):
    __tablename__ = "vend_transactions"
    __table_args__ = (
        Index("ix_vend_txn_machine_date", "machine_id", "txn_date"),
        Index("ix_vend_txn_product_date", "product_id", "txn_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Source identifiers (OrderId, OrderNo)
    source_order_id: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    order_no: Mapped[str | None] = mapped_column(String(100), nullable=True)

    machine_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("machines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raw_item_name: Mapped[str] = mapped_column(Text, nullable=False)  # original "Item Name" incl. price text
    bin_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    op_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timing (Date, Time, DateVal, Hour, Weekday, WeekType)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    txn_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    txn_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hour_of_day: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    weekday: Mapped[str | None] = mapped_column(String(15), nullable=True)
    week_type: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # Quantities & reliability (Order/Success/Failed Quantity, MachineFail, Lost Value)
    order_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    machine_fail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lost_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Money (Amount, PaidAmount, Net Revenue, C_Prd_MRP at time of sale)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    mrp_at_sale: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=VendStatus.SUCCESS, index=True)
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default=VendPaymentStatus.SUCCESS)
    refund_status: Mapped[str] = mapped_column(String(30), nullable=False, default=VendRefundStatus.NONE)
    refunded_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_refund_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment details
    payment_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prepaid_card_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prepaid_card_uid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utr_bank_transfer_no: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Device / source metadata
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    machine: Mapped["Machine"] = relationship("Machine")  # type: ignore[name-defined]
    product: Mapped["Product | None"] = relationship("Product", back_populates="vend_transactions")  # type: ignore[name-defined]
    import_batch: Mapped["ImportBatch | None"] = relationship("ImportBatch")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<VendTransaction order_no={self.order_no} machine_id={self.machine_id}>"


class ImportBatch(Base):
    """
    Tracks each Excel upload — one row per file/sheet processed. Makes
    re-imports and partial-failure recovery auditable at 100k-row volume.
    """

    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inserted_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skipped_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="processing")
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ImportBatch file={self.file_name} status={self.status}>"
