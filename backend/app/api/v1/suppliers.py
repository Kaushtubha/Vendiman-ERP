"""
app/api/v1/suppliers.py — Supplier Management API
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.core.dependencies import CurrentUserDep, DBDep, PaginationDep
from app.core.response import created_response, paginated_response, success_response
from app.domain.enums import SupplierRating, SupplierStatus
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


class SupplierCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    country: str = "India"
    gst_number: str | None = None
    pan_number: str | None = None
    state_code: str | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    status: SupplierStatus = SupplierStatus.ACTIVE
    rating: SupplierRating = SupplierRating.GOOD
    payment_terms_days: int = Field(default=30, ge=0)
    notes: str | None = None


class SupplierUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    contact_person: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    country: str | None = None
    gst_number: str | None = None
    pan_number: str | None = None
    state_code: str | None = None
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    status: SupplierStatus | None = None
    rating: SupplierRating | None = None
    payment_terms_days: int | None = Field(default=None, ge=0)
    notes: str | None = None


@router.get("", summary="List suppliers")
async def list_suppliers(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    rating: str | None = Query(default=None),
):
    service = SupplierService(db)
    items, total = await service.list_suppliers(
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
        status=status,
        rating=rating,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="Suppliers retrieved successfully",
    )


@router.post("", summary="Create supplier", status_code=status.HTTP_201_CREATED)
async def create_supplier(
    body: SupplierCreateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = SupplierService(db)
    result = await service.create_supplier(body.model_dump())
    return created_response(data=result, message="Supplier created successfully")


@router.get("/{supplier_id}", summary="Get supplier details")
async def get_supplier(
    supplier_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = SupplierService(db)
    result = await service.get_supplier(supplier_id)
    return success_response(data=result, message="Supplier details retrieved")


@router.put("/{supplier_id}", summary="Update supplier")
async def update_supplier(
    supplier_id: uuid.UUID,
    body: SupplierUpdateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = SupplierService(db)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await service.update_supplier(supplier_id, data)
    return success_response(data=result, message="Supplier updated successfully")
