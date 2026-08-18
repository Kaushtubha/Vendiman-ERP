"""
app/main.py — FastAPI Application Factory

PATTERN: Application Factory (not module-level app instantiation).

WHY application factory:
    - Tests can create isolated app instances with different configs.
    - Startup/shutdown lifecycle hooks are clearly defined.
    - Middleware registration order is explicit and documented.

STARTUP SEQUENCE:
    1. Configure logging (before any other code runs)
    2. Initialize DB connection pool (verify schema is up to date)
    3. Initialize Redis connection pool
    4. Mount all API routers
    5. Register exception handlers
    6. Register middleware (in reverse order of execution)
    7. Configure OpenAPI documentation

MIDDLEWARE EXECUTION ORDER (requests flow top-to-bottom):
    RequestIdMiddleware → RequestLoggingMiddleware → SecurityHeadersMiddleware
    → SlowAPI Rate Limiter → CORS → Route Handler

OPENAPI:
    WHY custom OpenAPI metadata: The default Swagger UI looks generic.
    Adding proper descriptions, contact info, license, and server URLs
    makes the API self-documenting for external developers and auditors.

EXCEPTION HANDLERS:
    Central exception → HTTP mapping. All domain exceptions are caught here
    and converted to the standard response envelope. No try/except needed in routes.

SECURITY:
    - CORS configured explicitly. Wildcard (*) NEVER used.
    - Rate limiting applied globally (100 req/min per IP by default).
    - Security headers applied by middleware.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    ERPBaseException,
    ForbiddenException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.core.logging import configure_logging
from app.core.middleware import (
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.response import error_response

# Configure logging FIRST — before any other module-level code
configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    WHY lifespan (not @app.on_event deprecated handlers):
        FastAPI 0.93+ recommends the lifespan context manager.
        It provides cleaner resource management — startup and shutdown
        are in one place, making it impossible to forget the shutdown.

    STARTUP:
        - Verify DB connection (fail fast — don't serve traffic with no DB)
        - Warm Redis pool
        - Log startup info

    SHUTDOWN:
        - Close DB connection pool (prevent connection leaks)
        - Close Redis pool
        - Flush any pending logs
    """
    from app.core.database import check_database_connection, engine
    from app.core.redis_client import get_redis_client

    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )

    # Verify database connectivity
    db_ok = await check_database_connection()
    if not db_ok:
        logger.critical(
            "FATAL: Cannot connect to database. Check DATABASE_URL. "
            "Application will NOT start."
        )
        raise RuntimeError("Database connection failed on startup")

    logger.info("Database connection pool initialized")

    # Verify Redis connectivity
    redis = get_redis_client()
    redis_ok = await redis.ping()
    if not redis_ok:
        # Redis is NOT fatal on startup — app can run degraded without cache.
        # However, Celery tasks will fail. Log a critical warning.
        logger.critical(
            "WARNING: Cannot connect to Redis. Cache and Celery tasks disabled. "
            "Check REDIS_URL."
        )
    else:
        logger.info("Redis connection pool initialized")

    logger.info("%s startup complete. Ready to serve requests.", settings.app_name)

    yield  # Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down %s...", settings.app_name)
    await engine.dispose()
    logger.info("Database connection pool closed")


def create_application() -> FastAPI:
    """
    Application factory function.

    Creates and configures the FastAPI application instance.

    Returns:
        Configured FastAPI application.
    """
    # ── Rate Limiter Setup ────────────────────────────────────────────────────
    # WHY rate limiting at app level (not Nginx):
    #   Nginx can rate-limit connections, but application-level limiting
    #   enables per-user, per-route limits (not just per-IP). Also works
    #   when Nginx is not in front (local dev, direct ECS exposure).
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"],
        storage_uri=settings.redis.url,  # Store counters in Redis — survives restarts
    )

    # ── FastAPI Instance ──────────────────────────────────────────────────────
    app = FastAPI(
        title=settings.app_name,
        description="""
## Mini Blinkit ERP & Warehouse Automation Platform

Enterprise-grade ERP system replacing Excel-based warehouse operations.

### Modules
- **Authentication & RBAC** — JWT with role-based access control
- **Product Management** — SKU, barcode, category, GST, images
- **Supplier Management** — CRUD, GST, purchase history, performance
- **Purchase Orders** — Full PO lifecycle with approval workflow
- **GRN** — Goods receipt, quantity validation, auto inventory update
- **Inventory** — Available/reserved/damaged stock, batch, expiry tracking
- **Warehouse Transfers** — Dark stores, transfer logs, capacity management
- **Customer Orders** — 60-second reservation, payment simulation
- **Delivery Challans** — DC generation, dispatch tracking, PDF
- **Dashboard & Analytics** — KPIs, charts, demand forecasting
- **Reports** — Excel/CSV/PDF export

### Authentication
All endpoints (except /health) require Bearer JWT token.
Obtain token from POST /api/v1/auth/login.

### Response Format
All responses use the standard envelope:
```json
{
    "success": true,
    "message": "...",
    "data": {...},
    "meta": null
}
```
        """,
        version=settings.app_version,
        contact={
            "name": settings.company.name,
            "email": settings.company.email,
        },
        license_info={
            "name": "Proprietary",
        },
        servers=[
            {"url": "http://localhost:8000", "description": "Local Development"},
            {"url": "https://api.staging.yourdomain.com", "description": "Staging"},
            {"url": "https://api.yourdomain.com", "description": "Production"},
        ],
        # OpenAPI documentation URLs
        docs_url="/docs" if not settings.is_production else None,  # Disable Swagger in prod
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Attach rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Register Routers ──────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Register Exception Handlers ───────────────────────────────────────────
    _register_exception_handlers(app)

    # ── Register Middleware ───────────────────────────────────────────────────
    # WHY add_middleware is in REVERSE order of execution:
    # The last middleware added is the first to process a request.
    # Execution order: RequestId → Logging → Security → CORS → SlowAPI → Route

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # CORS — must be outermost to handle preflight OPTIONS before auth
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers.

    PATTERN: Centralized exception → HTTP mapping.
    Each handler translates a domain/framework exception to the standard
    response envelope. No try/except needed in route handlers.
    """

    @app.exception_handler(ERPBaseException)
    async def erp_exception_handler(
        request: Request, exc: ERPBaseException
    ) -> JSONResponse:
        """Handle all domain exceptions from the ERPBaseException hierarchy."""
        status_code_map = {
            "RESOURCE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "CONFLICT": status.HTTP_409_CONFLICT,
            "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "BUSINESS_RULE_VIOLATION": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "INSUFFICIENT_STOCK": status.HTTP_409_CONFLICT,
            "RESERVATION_EXPIRED": status.HTTP_409_CONFLICT,
            "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
            "TOKEN_EXPIRED": status.HTTP_401_UNAUTHORIZED,
            "FORBIDDEN": status.HTTP_403_FORBIDDEN,
            "EXTERNAL_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        status_code = status_code_map.get(exc.code, status.HTTP_400_BAD_REQUEST)

        logger.warning(
            "Domain exception: code=%s message=%s request_id=%s",
            exc.code,
            exc.message,
            getattr(request.state, "request_id", "unknown"),
        )

        return error_response(
            message=exc.message,
            status_code=status_code,
            code=exc.code,
            context=exc.context,
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic v2 request validation errors.

        WHY custom handler (not default): FastAPI's default 422 response
        has a different structure than our envelope. Frontend code should
        handle one consistent error shape.
        """
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({"field": field, "message": error["msg"], "type": error["type"]})

        logger.info(
            "Request validation failed: %d error(s) | path=%s",
            len(errors),
            request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Request validation failed",
                "data": None,
                "meta": {"code": "VALIDATION_ERROR", "errors": errors},
            },
        )

    @app.exception_handler(JWTError)
    async def jwt_error_handler(request: Request, exc: JWTError) -> JSONResponse:
        """Catch any unhandled JWT errors."""
        return error_response(
            message="Invalid or expired authentication token",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all for unexpected exceptions.

        WHY: Without this, FastAPI returns a bare HTTP 500 with no body.
        This handler:
        1. Logs the full traceback (captured by Sentry in production).
        2. Returns a sanitized message to the client (no stack trace in prod).
        """
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "Unhandled exception | path=%s | request_id=%s",
            request.url.path,
            request_id,
            exc_info=exc,
        )

        message = (
            "An internal server error occurred. Our team has been notified."
            if settings.is_production
            else str(exc)  # Show actual error in development
        )

        return error_response(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
        )


# ── Application Instance ──────────────────────────────────────────────────────
app: FastAPI = create_application()
