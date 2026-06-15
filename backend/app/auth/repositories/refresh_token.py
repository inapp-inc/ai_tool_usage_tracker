"""Refresh token repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_refresh_token
from app.models.auth import RefreshToken


class RefreshTokenRepository:
    """Data access for auth.refresh_tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_valid_by_token(self, token: str) -> RefreshToken | None:
        token_hash = hash_refresh_token(token)
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, refresh_token: RefreshToken) -> RefreshToken:
        self._session.add(refresh_token)
        await self._session.flush()
        return refresh_token

    async def revoke(self, refresh_token: RefreshToken, when: datetime) -> None:
        refresh_token.revoked_at = when
        await self._session.flush()

    @staticmethod
    def store_hash(token: str) -> str:
        return hash_refresh_token(token)
