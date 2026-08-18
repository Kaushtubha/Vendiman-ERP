"""
app/services/product_service.py — Product & Catalog Business Logic
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    async def list_products(
        self,
        offset: int = 0,
        limit: int = 25,
        search: str | None = None,
        category_id: uuid.UUID | None = None,
        status: str | None = None,
        is_perishable: bool | None = None,
    ) -> tuple[list[dict], int]:
        products, total = await self.repo.get_all(
            offset=offset,
            limit=limit,
            search=search,
            category_id=category_id,
            status=status,
            is_perishable=is_perishable,
        )
        return [
            {
                "id": str(p.id),
                "sku": p.sku,
                "barcode": p.barcode,
                "name": p.name,
                "description": p.description,
                "category_id": str(p.category_id) if p.category_id else None,
                "category_name": p.category.name if p.category else None,
                "brand": p.brand,
                "unit": p.unit,
                "mrp": float(p.mrp),
                "cost_price": float(p.cost_price),
                "selling_price": float(p.selling_price),
                "gst_rate": p.gst_rate,
                "hsn_code": p.hsn_code,
                "status": p.status,
                "is_perishable": p.is_perishable,
                "shelf_life_days": p.shelf_life_days,
                "reorder_point": p.reorder_point,
                "reorder_quantity": p.reorder_quantity,
                "min_stock": p.min_stock,
                "image_url": p.image_url,
                "weight_grams": p.weight_grams,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ], total

    async def get_product(self, product_id: uuid.UUID) -> dict:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ResourceNotFoundException("Product", str(product_id))
        return {
            "id": str(product.id),
            "sku": product.sku,
            "barcode": product.barcode,
            "name": product.name,
            "description": product.description,
            "category_id": str(product.category_id) if product.category_id else None,
            "category_name": product.category.name if product.category else None,
            "brand": product.brand,
            "unit": product.unit,
            "mrp": float(product.mrp),
            "cost_price": float(product.cost_price),
            "selling_price": float(product.selling_price),
            "gst_rate": product.gst_rate,
            "hsn_code": product.hsn_code,
            "status": product.status,
            "is_perishable": product.is_perishable,
            "shelf_life_days": product.shelf_life_days,
            "reorder_point": product.reorder_point,
            "reorder_quantity": product.reorder_quantity,
            "min_stock": product.min_stock,
            "image_url": product.image_url,
            "weight_grams": product.weight_grams,
            "created_at": product.created_at.isoformat() if product.created_at else None,
        }

    async def get_by_barcode(self, barcode: str) -> dict:
        product = await self.repo.get_by_barcode(barcode)
        if not product:
            raise ResourceNotFoundException("Product", barcode, message=f"Product with barcode '{barcode}' not found")
        return await self.get_product(product.id)

    async def create_product(self, data: dict[str, Any]) -> dict:
        sku = data["sku"].upper()
        if await self.repo.exists_by_sku(sku):
            raise ConflictException(f"Product with SKU '{sku}' already exists", field="sku", value=sku)
        
        product = await self.repo.create(**data)
        logger.info("Created product sku=%s id=%s", product.sku, product.id)
        return await self.get_product(product.id)

    async def update_product(self, product_id: uuid.UUID, data: dict[str, Any]) -> dict:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ResourceNotFoundException("Product", str(product_id))

        if "sku" in data and data["sku"].upper() != product.sku:
            sku = data["sku"].upper()
            if await self.repo.exists_by_sku(sku, exclude_id=product_id):
                raise ConflictException(f"Product with SKU '{sku}' already exists", field="sku", value=sku)

        updated = await self.repo.update(product_id, **data)
        if not updated:
            raise ResourceNotFoundException("Product", str(product_id))
        return await self.get_product(product_id)

    async def list_categories(self) -> list[dict]:
        categories = await self.repo.get_all_categories()
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
            }
            for c in categories
        ]

    async def create_category(self, name: str, slug: str, description: str | None = None) -> dict:
        category = await self.repo.create_category(name=name, slug=slug, description=description)
        return {
            "id": str(category.id),
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
        }
