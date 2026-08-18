"""
app/api/v1/auth.py — Authentication Routes

Endpoints:
    POST /auth/login          → issue access + refresh tokens
    POST /auth/refresh        → exchange refresh token for new access token
    POST /auth/logout         → revoke tokens
    POST /auth/register       → create new user (ADMIN only)
    GET  /auth/me             → get current user profile
    PUT  /auth/me             → update own profile
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel, EmailStr, Field

from app.core.dependencies import (
    AdminDep,
    CurrentUserDep,
    DBDep,
    RedisDep,
    get_current_user_payload,
)
from app.core.response import created_response, success_response
from app.domain.enums import UserRole
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request/Response Schemas ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER
    phone: str | None = Field(default=None, max_length=20)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=20)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", summary="Login with email and password")
async def login(
    body: LoginRequest,
    db: DBDep,
    redis: RedisDep,
):
    service = AuthService(db, redis)
    result = await service.login(body.email, body.password)
    return success_response(data=result, message="Login successful")


@router.post("/refresh", summary="Refresh access token")
async def refresh_token(
    body: RefreshRequest,
    db: DBDep,
    redis: RedisDep,
):
    service = AuthService(db, redis)
    result = await service.refresh_access_token(body.refresh_token)
    return success_response(data=result, message="Token refreshed")


@router.post("/logout", summary="Logout and revoke tokens")
async def logout(
    body: LogoutRequest,
    payload: Annotated[dict, Depends(get_current_user_payload)],
    db: DBDep,
    redis: RedisDep,
):
    jti = payload.get("jti", "")
    exp = payload.get("exp", 0)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    ttl = max(0, exp - now_ts)

    service = AuthService(db, redis)
    await service.logout(body.refresh_token, jti, ttl)
    return success_response(message="Logged out successfully")


@router.post("/register", summary="Register a new user (Admin only)", status_code=201)
async def register(
    body: RegisterRequest,
    db: DBDep,
    redis: RedisDep,
    _: AdminDep,
):
    service = AuthService(db, redis)
    user_data = await service.register(
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        role=body.role,
        phone=body.phone,
    )
    return created_response(data=user_data, message="User registered successfully")


@router.get("/me", summary="Get current user profile")
async def get_me(
    current_user: CurrentUserDep,
    db: DBDep,
):
    from app.repositories.user_repository import UserRepository
    import uuid

    user_id = uuid.UUID(current_user["sub"])
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        from app.core.exceptions import ResourceNotFoundException
        raise ResourceNotFoundException("User", str(user_id))

    return success_response(
        data={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
        },
        message="Profile retrieved",
    )


@router.put("/me", summary="Update own profile")
async def update_me(
    body: UpdateProfileRequest,
    current_user: CurrentUserDep,
    db: DBDep,
):
    from app.repositories.user_repository import UserRepository
    import uuid

    user_id = uuid.UUID(current_user["sub"])
    repo = UserRepository(db)

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    user = await repo.update(user_id, **updates)

    return success_response(
        data={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
        },
        message="Profile updated",
    )
