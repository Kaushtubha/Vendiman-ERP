"""
app/api/v1/upload.py — Bulk Excel Upload API
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.dependencies import CurrentUserDep, DBDep
from app.core.exceptions import ValidationException
from app.core.response import success_response
from app.repositories.product_repository import ProductRepository
from app.utils.excel_parser import parse_product_excel

router = APIRouter(prefix="/upload", tags=["Bulk Uploads"])


@router.post("/products-excel", summary="Upload products via Excel (.xlsx)")
async def upload_products_excel(
    file: UploadFile = File(...),
    db: DBDep = None,  # type: ignore[assignment]
    current_user: CurrentUserDep = None,  # type: ignore[assignment]
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise ValidationException("Only .xlsx or .xls files are supported", field="file")

    contents = await file.read()
    parsed_items = parse_product_excel(contents)

    if not parsed_items:
        raise ValidationException("No valid product rows found in Excel sheet", field="file")

    repo = ProductRepository(db)
    created_count = 0
    updated_count = 0

    for item in parsed_items:
        existing = await repo.get_by_sku(item["sku"])
        if existing:
            await repo.update(existing.id, **item)
            updated_count += 1
        else:
            await repo.create(**item)
            created_count += 1

    return success_response(
        data={
            "total_processed": len(parsed_items),
            "created_count": created_count,
            "updated_count": updated_count,
        },
        message=f"Excel processed successfully: {created_count} created, {updated_count} updated",
    )
