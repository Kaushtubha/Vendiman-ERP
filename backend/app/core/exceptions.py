"""
app/core/exceptions.py — Domain Exception Hierarchy

PATTERN: Rich domain exception hierarchy mapped to HTTP exceptions via handlers.

WHY a custom exception hierarchy:
    1. SEPARATION OF CONCERNS: Domain layer (services, repositories) raises domain
       exceptions (e.g., InsufficientStockError). The API layer catches them and
       maps to HTTP responses. Domain code knows nothing about HTTP status codes.

    2. STRUCTURED ERROR CONTEXT: Each exception carries structured metadata —
       not just a message string. This enables machine-readable error responses
       that frontend clients can programmatically handle (not just display).

    3. CENTRALIZED MAPPING: One exception handler in main.py converts all domain
       exceptions to a consistent response envelope. No try/except boilerplate
       in every route.

    4. TESTABILITY: Unit tests can assert `raises(InsufficientStockError)` with
       specific context data, independent of HTTP layer.

HIERARCHY:
    ERPBaseException
    ├── ResourceNotFoundException       → 404
    ├── ValidationException             → 422
    ├── ConflictException               → 409
    ├── ForbiddenException              → 403
    ├── UnauthorizedException           → 401
    ├── BusinessRuleViolationException  → 422
    └── ExternalServiceException        → 503

SCALABILITY:
    New exceptions are added to this file only. The handler in main.py
    automatically handles all subclasses of ERPBaseException. No handler
    changes required for new exception types.
"""

from __future__ import annotations

from typing import Any


class ERPBaseException(Exception):
    """
    Base class for all application-specific exceptions.

    Attributes:
        message: Human-readable error message (safe to display to users)
        code: Machine-readable error code (used by frontend for i18n/handling)
        context: Structured data providing additional error context
    """

    default_message: str = "An unexpected error occurred"
    default_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception for JSON error response."""
        return {
            "code": self.code,
            "message": self.message,
            "context": self.context,
        }


# ── 404 Not Found ─────────────────────────────────────────────────────────────
class ResourceNotFoundException(ERPBaseException):
    """
    Raised when a requested resource does not exist.

    Usage:
        raise ResourceNotFoundException("Product", product_id)
    """

    default_code = "RESOURCE_NOT_FOUND"

    def __init__(
        self,
        resource_type: str,
        resource_id: str | int | None = None,
        message: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        ctx = {"resource_type": resource_type, "resource_id": str(resource_id), **(context or {})}
        msg = message or (
            f"{resource_type} with id '{resource_id}' not found"
            if resource_id
            else f"{resource_type} not found"
        )
        super().__init__(message=msg, code=self.default_code, context=ctx)


# ── 409 Conflict ──────────────────────────────────────────────────────────────
class ConflictException(ERPBaseException):
    """
    Raised when an operation would violate a uniqueness constraint.
    Examples: duplicate SKU, duplicate PO number, duplicate email.
    """

    default_code = "CONFLICT"
    default_message = "Resource already exists"

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = {"field": field, "value": value, **(context or {})}
        super().__init__(message=message, code=self.default_code, context=ctx)


# ── 422 Validation / Business Rule ───────────────────────────────────────────
class ValidationException(ERPBaseException):
    """
    Raised when input data is structurally valid but semantically invalid.
    (Pydantic handles structural validation — this handles business rules.)

    Examples: PO date in the past, GRN quantity exceeds PO quantity.
    """

    default_code = "VALIDATION_ERROR"
    default_message = "Validation failed"

    def __init__(
        self,
        message: str,
        field: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = {"field": field, **(context or {})}
        super().__init__(message=message, code=self.default_code, context=ctx)


class BusinessRuleViolationException(ERPBaseException):
    """
    Raised when a domain business rule is violated.

    More specific than ValidationException — this represents an invariant
    of the business domain being broken.

    Examples:
        - Approving an already-approved PO
        - Receiving GRN for a cancelled PO
        - Transferring more stock than available
        - Stock reservation for out-of-stock item
    """

    default_code = "BUSINESS_RULE_VIOLATION"
    default_message = "Business rule violated"


class InsufficientStockException(BusinessRuleViolationException):
    """
    Raised when stock operations require more quantity than available.
    Provides structured context: product, warehouse, requested vs available.
    """

    default_code = "INSUFFICIENT_STOCK"

    def __init__(
        self,
        product_id: str,
        warehouse_id: str,
        requested: int,
        available: int,
    ) -> None:
        super().__init__(
            message=(
                f"Insufficient stock: requested {requested}, "
                f"but only {available} available"
            ),
            context={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "requested": requested,
                "available": available,
            },
        )


class StockReservationExpiredException(BusinessRuleViolationException):
    """Raised when a customer tries to pay after reservation has expired."""

    default_code = "RESERVATION_EXPIRED"

    def __init__(self, order_id: str) -> None:
        super().__init__(
            message="Stock reservation has expired. Please retry your order.",
            context={"order_id": order_id},
        )


# ── 401 Unauthorized ──────────────────────────────────────────────────────────
class UnauthorizedException(ERPBaseException):
    """Raised when authentication fails or token is invalid/expired."""

    default_code = "UNAUTHORIZED"
    default_message = "Authentication required"


class TokenExpiredException(UnauthorizedException):
    """Raised specifically when JWT token has expired (frontend can refresh)."""

    default_code = "TOKEN_EXPIRED"
    default_message = "Access token has expired. Please refresh."


# ── 403 Forbidden ─────────────────────────────────────────────────────────────
class ForbiddenException(ERPBaseException):
    """
    Raised when an authenticated user lacks permission for an action.

    WHY distinguish 401 vs 403:
        401: "Who are you? Please log in."
        403: "I know who you are, but you can't do this."
    """

    default_code = "FORBIDDEN"
    default_message = "You do not have permission to perform this action"

    def __init__(
        self,
        message: str | None = None,
        required_role: str | None = None,
        action: str | None = None,
    ) -> None:
        ctx = {"required_role": required_role, "action": action}
        super().__init__(
            message=message or self.default_message,
            code=self.default_code,
            context=ctx,
        )


# ── 503 External Service Error ────────────────────────────────────────────────
class ExternalServiceException(ERPBaseException):
    """
    Raised when an external service (email, PDF service, S3) fails.

    WHY separate: Allows retry logic and circuit breaker patterns to be applied
    specifically to external service failures without masking internal bugs.
    """

    default_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "External service unavailable. Please try again."
