"""
app/core/middleware.py — Request/Response Middleware

PATTERN: ASGI Middleware stack for cross-cutting concerns.

MIDDLEWARE ORDER MATTERS — executed in reverse registration order:
    Request flow:  RequestLoggingMiddleware → RateLimitMiddleware → Route
    Response flow: Route → RateLimitMiddleware → RequestLoggingMiddleware

WHY middleware (not route decorators):
    Cross-cutting concerns (logging, rate limiting, correlation IDs) affect ALL
    routes. Middleware applies them once. Route decorators would duplicate
    logic across hundreds of route functions.

INCLUDED MIDDLEWARE:
    1. RequestIdMiddleware: Adds X-Request-ID to every request/response.
       Critical for correlating logs across services.
    2. RequestLoggingMiddleware: Logs method, path, status, duration.
    3. SecurityHeadersMiddleware: Adds security HTTP headers to all responses.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique request ID to every request and response.

    WHY request ID:
        - Correlates all log lines for a single request across services.
        - Frontend sends X-Request-ID in error reports for debugging.
        - Support teams reference request IDs when investigating incidents.

    The ID is taken from the incoming X-Request-ID header (if present, e.g.,
    from a load balancer) or generated as a new UUID.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Attach to request state for use in route handlers and logging
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request with method, path, status code, and duration.

    WHY log at middleware level (not route level):
        Middleware captures ALL requests including 404s and framework errors
        that never reach a route handler. Route-level logging misses these.

    SECURITY:
        - Never log query parameters or request bodies (may contain PII/secrets).
        - Only log path, method, status, duration, and request ID.

    PERFORMANCE:
        - time.perf_counter() for sub-millisecond precision.
        - Log only at WARNING level for slow requests (>2s) to enable alerting.
    """

    SLOW_REQUEST_THRESHOLD_MS = 2000  # Alert if response takes > 2 seconds

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        log_method = (
            logger.warning
            if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS or status_code >= 500
            else logger.info
        )

        log_method(
            "%s %s %s %.2fms | req_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )

        # Expose timing to clients (useful for performance monitoring)
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security HTTP headers to all responses.

    WHY:
        Security headers prevent common web vulnerabilities:
        - CSP: Prevents XSS by restricting script sources.
        - HSTS: Forces HTTPS on subsequent visits (prevents SSL stripping).
        - X-Frame-Options: Prevents clickjacking.
        - X-Content-Type-Options: Prevents MIME sniffing attacks.
        - Referrer-Policy: Controls referrer information sent with requests.
        - Permissions-Policy: Disables browser features not used by the API.

    NOTE: For the React SPA (served separately), these headers are set on
    the Nginx/CDN layer, not the API. This middleware protects the API itself.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        # Only apply to API responses (not file uploads/downloads)
        if "application/json" in response.headers.get("content-type", ""):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=()"
            )
            # HSTS: Tell browsers to only use HTTPS for 1 year
            # ONLY set in production — breaks local HTTP dev
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )

        return response
