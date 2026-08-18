"""
app/api/v1/products.py — Product Management API
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, DBDep, PaginationDep
from app.core.response import created_response, paginated_response, success_response
from app.domain.enums import GSTRate, ProductStatus
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductCreateRequest(BaseModel):
    sku: str = Field(min_length=2, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    brand: str | None = Field(default=None, max_length=100)
    unit: str = Field(default="piece", max_length=50)
    mrp: Decimal = Field(gt=0)
    cost_price: Decimal = Field(gt=0)
    selling_price: Decimal = Field(gt=0)
    gst_rate: GSTRate = GSTRate.EIGHTEEN
    hsn_code: str | None = Field(default=None, max_length=20)
    status: ProductStatus = ProductStatus.ACTIVE
    is_perishable: bool = False
    shelf_life_days: int | None = Field(default=None, ge=1)
    reorder_point: int = Field(default=10, ge=0)
    reorder_quantity: int = Field(default=50, ge=1)
    min_stock: int = Field(default=5, ge=0)
    image_url: str | None = None
    weight_grams: int | None = Field(default=None, ge=0)


class ProductUpdateRequest(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    brand: str | None = None
    unit: str | None = None
    mrp: Decimal | None = Field(default=None, gt=0)
    cost_price: Decimal | None = Field(default=None, gt=0)
    selling_price: Decimal | None = Field(default=None, gt=0)
    gst_rate: GSTRate | None = None
    hsn_code: str | None = None
    status: ProductStatus | None = None
    is_perishable: bool | None = None
    shelf_life_days: int | None = None
    reorder_point: int | None = Field(default=None, ge=0)
    reorder_quantity: int | None = Field(default=None, ge=1)
    min_stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    weight_grams: int | None = None


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    description: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", summary="List products with filters and pagination")
async def list_products(
    db: DBDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    search: str | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    is_perishable: bool | None = Query(default=None),
):
    service = ProductService(db)
    items, total = await service.list_products(
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
        category_id=category_id,
        status=status,
        is_perishable=is_perishable,
    )
    return paginated_response(
        data=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        message="Products retrieved successfully",
    )


@router.post("", summary="Create a new product", status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    data = body.model_dump()
    result = await service.create_product(data)
    return created_response(data=result, message="Product created successfully")


@router.get("/categories", summary="List all active product categories")
async def list_categories(
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    categories = await service.list_categories()
    return success_response(data=categories, message="Categories retrieved successfully")


@router.post("/categories", summary="Create product category", status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    category = await service.create_category(name=body.name, slug=body.slug, description=body.description)
    return created_response(data=category, message="Category created successfully")


@router.get("/barcode/{barcode}", summary="Lookup product by barcode")
async def lookup_barcode(
    barcode: str,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    result = await service.get_by_barcode(barcode)
    return success_response(data=result, message="Product found")


@router.get("/{product_id}", summary="Get product details by ID")
async def get_product(
    product_id: uuid.UUID,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    result = await service.get_product(product_id)
    return success_response(data=result, message="Product details retrieved")


@router.put("/{product_id}", summary="Update product")
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdateRequest,
    db: DBDep,
    current_user: CurrentUserDep,
):
    service = ProductService(db)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await service.update_product(product_id, data)
    return success_response(data=result, message="Product updated successfully")
