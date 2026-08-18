"""
app/core/response.py — Unified API Response Envelope

PATTERN: Response Envelope (also known as JSend / API Result wrapper).

WHY a response envelope:
    1. CONSISTENCY: Every API response has the same top-level shape:
         { success, data, message, meta }
       Frontend clients never need to special-case response structure.

    2. PAGINATION METADATA: List endpoints include page/total/limit in
       the `meta` field — not in custom headers (harder to consume in JS).

    3. ERROR SHAPE: Errors follow the same envelope with success=false.
       Frontend catches errors by checking response.success, not HTTP status code.
       HTTP status codes are still set correctly — they're the primary signal.

    4. VERSIONING SAFETY: Adding new top-level fields (e.g., `warnings`) is
       backward-compatible. Clients that ignore unknown fields keep working.

WHY NOT:
    - Returning bare objects (e.g., `return product`): Works fine until you
      need to add pagination or metadata. Retrofitting an envelope breaks all
      existing clients.
    - FastAPI's default response: No envelope. Acceptable for simple APIs,
      but inconsistent at scale.

EXAMPLE RESPONSES:

    Single object:
    {
        "success": true,
        "message": "Product retrieved",
        "data": { "id": "...", "name": "Milk" },
        "meta": null
    }

    Paginated list:
    {
        "success": true,
        "message": "Products retrieved",
        "data": [...],
        "meta": { "page": 1, "limit": 25, "total": 150, "total_pages": 6 }
    }

    Error:
    {
        "success": false,
        "message": "Product not found",
        "data": null,
        "meta": { "code": "RESOURCE_NOT_FOUND", "resource_type": "Product" }
    }
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """
    Metadata for paginated list responses.

    WHY offset-based pagination (not cursor-based):
        For this ERP system, users navigate by page number ("Go to page 5").
        Cursor-based pagination only supports "next/previous" navigation,
        which is appropriate for infinite scroll (social feeds) but not for
        tabular ERP data where jumping to page 50 is a valid operation.

        SCALABILITY NOTE: Offset pagination degrades at millions of rows
        (OFFSET 1000000 LIMIT 25 scans 1M rows). For the analytics module,
        cursor pagination will be used for streaming large exports.
    """

    page: int = Field(ge=1, description="Current page number (1-indexed)")
    limit: int = Field(ge=1, description="Items per page")
    total: int = Field(ge=0, description="Total items matching the query")
    total_pages: int = Field(ge=0, description="Total pages")
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "PaginationMeta":
        total_pages = max(1, (total + limit - 1) // limit)
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class APIResponse(BaseModel, Generic[T]):
    """
    Generic API response envelope.

    Generic[T] allows Pydantic to validate the `data` field as a specific type,
    enabling accurate OpenAPI schema generation. FastAPI uses this for Swagger.

    Example typing: APIResponse[ProductResponse] generates a Swagger schema
    showing the exact shape of the nested product object.
    """

    success: bool
    message: str
    data: T | None = None
    meta: dict[str, Any] | PaginationMeta | None = None


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: dict[str, Any] | PaginationMeta | None = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    Build a successful JSON response.

    Uses JSONResponse with orjson serialization for 2x faster serialization
    compared to the default Python json module. Critical for list endpoints
    returning 200+ objects.
    """
    content = {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta.model_dump() if isinstance(meta, PaginationMeta) else meta,
    }
    return JSONResponse(content=content, status_code=status_code)


def created_response(
    data: Any = None,
    message: str = "Created successfully",
) -> JSONResponse:
    """Convenience wrapper for 201 Created responses."""
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    code: str = "ERROR",
    context: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build an error JSON response in the standard envelope format."""
    meta: dict[str, Any] = {"code": code}
    if context:
        meta.update(context)

    content = {
        "success": False,
        "message": message,
        "data": None,
        "meta": meta,
    }
    return JSONResponse(content=content, status_code=status_code)


def paginated_response(
    data: list[Any],
    total: int,
    page: int,
    limit: int,
    message: str = "Data retrieved successfully",
) -> JSONResponse:
    """
    Build a paginated list response with PaginationMeta.

    Args:
        data: The current page of results.
        total: Total items matching the query (for page count).
        page: Current page number (1-indexed).
        limit: Items per page.
        message: Optional success message.
    """
    pagination = PaginationMeta.create(page=page, limit=limit, total=total)
    return success_response(data=data, message=message, meta=pagination)
