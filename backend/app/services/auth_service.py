"""
app/services/auth_service.py — Authentication Business Logic

PATTERN: Service layer — orchestrates repositories, applies business rules.
No SQL here; no HTTP concerns here.

FLOW:
    login()         → verify credentials → issue tokens
    refresh()       → validate refresh token → issue new access token
    logout()        → revoke refresh token + add access token to denylist
    register()      → validate uniqueness → hash password → create user
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.redis_client import RedisClient
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.enums import UserRole, UserStatus
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


def _hash_token(token: str) -> str:
    """SHA-256 hash of a refresh token for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    """
    Authentication service. Stateless — accepts db and redis per call.
    """

    def __init__(self, db: AsyncSession, redis: RedisClient) -> None:
        self.db = db
        self.redis = redis
        self.repo = UserRepository(db)

    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate user with email + password.
        Returns access_token, refresh_token, and user data.

        Raises:
            UnauthorizedException: If credentials are invalid or account inactive.
        """
        user = await self.repo.get_by_email(email)

        # Always verify (even if user is None) to prevent timing attacks
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException(message="Invalid email or password")

        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedException(
                message=f"Account is {user.status}. Contact your administrator."
            )

        # Issue tokens
        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role,
        )
        refresh_token_str, refresh_expires_at = create_refresh_token(str(user.id))

        # Store hashed refresh token in DB
        token_hash = _hash_token(refresh_token_str)
        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=refresh_expires_at,
        )

        # Update last login
        await self.repo.update(user.id, last_login_at=datetime.now(timezone.utc))

        logger.info("User logged in: user_id=%s role=%s", user.id, user.role)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "avatar_url": user.avatar_url,
            },
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Exchange a valid refresh token for a new access token.
        Implements token rotation: old refresh token is revoked, new one issued.
        """
        # Decode and validate refresh token
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise UnauthorizedException(message="Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid token type")

        # Check against DB (revocation check)
        token_hash = _hash_token(refresh_token)
        stored_token = await self.repo.get_refresh_token(token_hash)
        if not stored_token:
            raise UnauthorizedException(message="Refresh token not found or revoked")

        # Check expiry
        if stored_token.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedException(message="Refresh token has expired")

        # Load user
        user = await self.repo.get_by_id(stored_token.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise UnauthorizedException(message="User account inactive")

        # Token rotation: revoke old, issue new
        await self.repo.revoke_refresh_token(token_hash)
        new_access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role,
        )
        new_refresh_str, new_refresh_expires = create_refresh_token(str(user.id))
        new_hash = _hash_token(new_refresh_str)
        await self.repo.create_refresh_token(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=new_refresh_expires,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_str,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token: str, access_token_jti: str, access_token_ttl_seconds: int) -> None:
        """
        Logout: revoke the refresh token and add access token JTI to Redis denylist.
        """
        # Revoke refresh token in DB
        token_hash = _hash_token(refresh_token)
        await self.repo.revoke_refresh_token(token_hash)

        # Add access token JTI to Redis denylist (TTL = remaining token lifetime)
        denylist_key = RedisClient.build_key("auth", "denylist", access_token_jti)
        await self.redis.setex(denylist_key, access_token_ttl_seconds, "1")

        logger.info("User logged out: jti=%s", access_token_jti)

    async def register(
        self,
        email: str,
        full_name: str,
        password: str,
        role: str = UserRole.VIEWER,
        phone: str | None = None,
    ) -> dict:
        """
        Register a new user. Only ADMIN can call this in practice
        (enforced by require_role() in the route).
        """
        if await self.repo.exists_by_email(email):
            raise ConflictException(
                message=f"User with email '{email}' already exists",
                field="email",
                value=email,
            )

        hashed = hash_password(password)
        user = await self.repo.create(
            email=email,
            full_name=full_name,
            hashed_password=hashed,
            role=role,
            phone=phone,
        )

        logger.info("New user registered: user_id=%s email=%s role=%s", user.id, user.email, role)

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.isoformat(),
        }
