"""
app/repositories/user_repository.py — User Data Access Layer

PATTERN: Repository pattern — all DB queries for the User aggregate
live here. Services call repositories. Routes call services.

WHY: Keeps SQL out of service logic. Repositories can be swapped for
test doubles. Services remain testable without a database.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import RefreshToken, User


class UserRepository:
    """
    Data access methods for User and RefreshToken entities.
    All methods are async and accept a db session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── User Queries ──────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch user by UUID primary key."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email (used during login)."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 25,
        role: str | None = None,
        status: str | None = None,
    ) -> tuple[list[User], int]:
        """
        Paginated user list with optional filters.
        Returns (users, total_count).
        """
        from sqlalchemy import func

        query = select(User)
        count_query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
            count_query = count_query.where(User.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> User:
        """Create and persist a new user."""
        if "email" in kwargs:
            kwargs["email"] = kwargs["email"].lower().strip()
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()  # Gets the generated ID without committing
        await self.db.refresh(user)
        return user

    async def update(self, user_id: uuid.UUID, **kwargs: Any) -> User | None:
        """Update user fields. Returns updated user or None if not found."""
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        return await self.get_by_id(user_id)

    async def exists_by_email(self, email: str) -> bool:
        """Check if email is already registered."""
        from sqlalchemy import exists as sql_exists
        result = await self.db.execute(
            select(sql_exists().where(User.email == email.lower().strip()))
        )
        return result.scalar_one()

    # ── Refresh Token ─────────────────────────────────────────────────────────

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: Any,
    ) -> RefreshToken:
        """Store a hashed refresh token."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        """Look up a refresh token by its hash."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Mark a refresh token as revoked (logout)."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all refresh tokens for a user (force logout all devices)."""
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
