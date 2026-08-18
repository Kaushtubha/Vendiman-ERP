"""
app/core/dependencies.py — FastAPI Dependency Injection

PATTERN: Dependency Injection via FastAPI's Depends() system.

WHY FastAPI DI (not global state):
    1. TESTABILITY: In tests, override get_db() to use a test database,
       override get_current_user() to return a mock user. No monkey-patching.
    2. LIFECYCLE MANAGEMENT: get_db() is a generator. FastAPI calls it before
       the route and closes the session after the response is sent.
    3. SCOPING: Each request gets its own DB session. No cross-request state.
    4. READABILITY: Route signatures explicitly declare their dependencies.
       `current_user: Annotated[User, Depends(get_current_user)]` is
       self-documenting.

SECURITY NOTE on RBAC:
    Role checking is done in require_role() dependency, NOT in route logic.
    This keeps authorization out of business logic and makes it auditable.
    All role requirements are visible from the route signature.

USAGE PATTERN (in route files):

    # Basic auth
    @router.get("/products")
    async def list_products(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        ...

    # With role requirement
    @router.post("/purchase-orders")
    async def create_po(
        db: AsyncSession = Depends(get_db),
        _: User = Depends(require_role(UserRole.PROCUREMENT)),
    ):
        ...

    # Common annotations for DRY usage
    DBDep = Annotated[AsyncSession, Depends(get_db)]
    CurrentUserDep = Annotated[User, Depends(get_current_user)]
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ForbiddenException, TokenExpiredException, UnauthorizedException
from app.core.redis_client import RedisClient, get_redis_client
from app.core.security import decode_token
from app.domain.enums import UserRole

logger = logging.getLogger(__name__)

# HTTP Bearer scheme — extracts "Bearer <token>" from Authorization header.
# auto_error=False: We handle the error ourselves for better error messages.
bearer_scheme = HTTPBearer(auto_error=False)


# ── Database Session ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a database session for the duration of a request.

    LIFECYCLE:
        1. FastAPI calls this before the route handler.
        2. Session is yielded into the route handler.
        3. After the response is sent, FastAPI resumes the generator.
        4. Session is closed (returning connection to pool).

    WHY generator (not context manager):
        FastAPI's Depends() handles the cleanup when a generator is used.
        The `finally` block runs even if an exception is raised in the route.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Authentication ────────────────────────────────────────────────────────────
async def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    redis: Annotated[RedisClient, Depends(get_redis_client)],
) -> dict:
    """
    Validate JWT token and return the decoded payload.

    WHY validate token type:
        Prevents using a refresh token as an access token. Both are valid JWTs
        signed with the same key, but have different `type` claims.

    WHY check Redis denylist:
        When a user logs out or an admin revokes a token, we add the jti to
        Redis with TTL = remaining token lifetime. This is the ONLY way to
        invalidate stateless JWTs without waiting for expiry.
    """
    if not credentials:
        raise UnauthorizedException(message="Authorization header missing")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        error_message = str(exc).lower()
        if "expired" in error_message:
            raise TokenExpiredException()
        raise UnauthorizedException(message="Invalid authentication token")

    # Verify token type
    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid token type")

    # Check token revocation denylist
    jti = payload.get("jti")
    if jti:
        denylist_key = RedisClient.build_key("auth", "denylist", jti)
        is_revoked = await redis.get(denylist_key)
        if is_revoked:
            raise UnauthorizedException(message="Token has been revoked")

    return payload


async def get_current_user(
    payload: Annotated[dict, Depends(get_current_user_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Return the current authenticated user's data.

    NOTE: In Module 2 (Authentication), this will load the full User model
    from the database using payload["sub"] (user UUID). In Module 1, it
    returns the JWT payload directly — sufficient for the health check.

    IMPORTANT: Never trust the role from the JWT payload alone for
    authorization decisions. Always reload from DB to get current role —
    the JWT role could be stale if the admin changed it after token issuance.
    (JWT role is only used for frontend UI hints, not server-side enforcement.)
    """
    return payload


# ── Role-Based Access Control ─────────────────────────────────────────────────
def require_role(*allowed_roles: UserRole):
    """
    Factory function that returns a dependency enforcing role restrictions.

    PATTERN: Dependency factory (higher-order function).
    WHY factory: require_role(UserRole.ADMIN, UserRole.MANAGER) is readable
    in route signatures. Alternative (decorator) would be less composable.

    WHY NOT check roles in the service layer:
        Services are reusable across contexts (API, Celery tasks, scripts).
        Authorization is a presentation concern — belongs at the API boundary.

    Usage:
        @router.delete("/products/{id}")
        async def delete_product(
            _: Annotated[dict, Depends(require_role(UserRole.ADMIN))],
        ):
    """
    allowed_role_values = {role.value for role in allowed_roles}

    async def role_checker(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_role = current_user.get("role")
        if user_role not in allowed_role_values:
            raise ForbiddenException(
                required_role=str(allowed_role_values),
                action=f"Access restricted to roles: {allowed_role_values}",
            )
        return current_user

    return role_checker


# ── Pagination ─────────────────────────────────────────────────────────────────
class PaginationParams:
    """
    Standard pagination parameters extracted from query string.

    WHY a class (not individual Depends):
        Groups related params. Easier to pass as a single dependency.
        Centralizes validation (page >= 1, limit <= max_page_size).

    Usage:
        @router.get("/products")
        async def list_products(pagination: PaginationDep):
            offset = pagination.offset
    """

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        limit: int = Query(default=25, ge=1, le=200, description="Items per page"),
    ) -> None:
        self.page = page
        self.limit = limit

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET from page and limit."""
        return (self.page - 1) * self.limit


# ── Type Aliases (DRY imports in route files) ─────────────────────────────────
# WHY Annotated aliases: Route signatures become:
#   async def list_products(db: DBDep, user: CurrentUserDep, p: PaginationDep)
# instead of verbose Depends() calls repeated in every route.

DBDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict, Depends(get_current_user)]
PaginationDep = Annotated[PaginationParams, Depends(PaginationParams)]
RedisDep = Annotated[RedisClient, Depends(get_redis_client)]
AdminDep = Annotated[dict, Depends(require_role(UserRole.ADMIN))]
