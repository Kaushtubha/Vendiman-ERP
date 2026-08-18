"""
app/services/supplier_service.py — Supplier Business Logic
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.repositories.supplier_repository import SupplierRepository

logger = logging.getLogger(__name__)


class SupplierService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SupplierRepository(db)

    async def list_suppliers(
        self,
        offset: int = 0,
        limit: int = 25,
        search: str | None = None,
        status: str | None = None,
        rating: str | None = None,
    ) -> tuple[list[dict], int]:
        suppliers, total = await self.repo.get_all(
            offset=offset,
            limit=limit,
            search=search,
            status=status,
            rating=rating,
        )
        return [
            {
                "id": str(s.id),
                "code": s.code,
                "name": s.name,
                "contact_person": s.contact_person,
                "email": s.email,
                "phone": s.phone,
                "gst_number": s.gst_number,
                "city": s.city,
                "state": s.state,
                "status": s.status,
                "rating": s.rating,
                "payment_terms_days": s.payment_terms_days,
                "total_orders": s.total_orders,
                "total_spend": float(s.total_spend),
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in suppliers
        ], total

    async def get_supplier(self, supplier_id: uuid.UUID) -> dict:
        s = await self.repo.get_by_id(supplier_id)
        if not s:
            raise ResourceNotFoundException("Supplier", str(supplier_id))
        return {
            "id": str(s.id),
            "code": s.code,
            "name": s.name,
            "contact_person": s.contact_person,
            "email": s.email,
            "phone": s.phone,
            "alternate_phone": s.alternate_phone,
            "address_line1": s.address_line1,
            "address_line2": s.address_line2,
            "city": s.city,
            "state": s.state,
            "pincode": s.pincode,
            "country": s.country,
            "gst_number": s.gst_number,
            "pan_number": s.pan_number,
            "state_code": s.state_code,
            "bank_name": s.bank_name,
            "bank_account_number": s.bank_account_number,
            "bank_ifsc": s.bank_ifsc,
            "status": s.status,
            "rating": s.rating,
            "payment_terms_days": s.payment_terms_days,
            "total_orders": s.total_orders,
            "total_spend": float(s.total_spend),
            "on_time_delivery_rate": float(s.on_time_delivery_rate) if s.on_time_delivery_rate else None,
            "notes": s.notes,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    async def create_supplier(self, data: dict[str, Any]) -> dict:
        code = data["code"].upper()
        if await self.repo.exists_by_code(code):
            raise ConflictException(f"Supplier with code '{code}' already exists", field="code", value=code)
        
        supplier = await self.repo.create(**data)
        return await self.get_supplier(supplier.id)

    async def update_supplier(self, supplier_id: uuid.UUID, data: dict[str, Any]) -> dict:
        supplier = await self.repo.get_by_id(supplier_id)
        if not supplier:
            raise ResourceNotFoundException("Supplier", str(supplier_id))

        if "code" in data and data["code"].upper() != supplier.code:
            code = data["code"].upper()
            if await self.repo.exists_by_code(code, exclude_id=supplier_id):
                raise ConflictException(f"Supplier with code '{code}' already exists", field="code", value=code)

        await self.repo.update(supplier_id, **data)
        return await self.get_supplier(supplier_id)
