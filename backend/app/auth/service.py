"""Authentication business logic."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories.refresh_token import RefreshTokenRepository
from app.auth.repositories.user import UserRepository
from app.auth.schemas import TokenResponse, UserProfile
from app.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    generate_opaque_refresh_token,
    hash_password,
    normalize_email,
    verify_password,
)
from app.models.auth import RefreshToken, User


@dataclass(frozen=True)
class AuthenticatedUser:
    """Current authenticated user context."""

    id: uuid.UUID
    email: str
    role: str
    organization_id: uuid.UUID
    display_name: str | None


class AuthService:
    """Login, refresh, and profile operations."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._users = UserRepository(session)
        self._refresh_tokens = RefreshTokenRepository(session)

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self._users.get_by_email(email)
        if user is None or not user.active:
            return None
        if not verify_password(user.password_hash, password):
            return None
        await self._users.update_last_login(user, datetime.now(UTC))
        return user

    async def issue_tokens(self, user: User) -> TokenResponse:
        access_token, expires_in = create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            role=user.role,
            settings=self._settings,
        )
        refresh_plain = generate_opaque_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.jwt_refresh_token_expire_days
        )
        refresh_row = RefreshToken(
            user_id=user.id,
            token_hash=RefreshTokenRepository.store_hash(refresh_plain),
            expires_at=expires_at,
        )
        await self._refresh_tokens.add(refresh_row)
        await self._session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_plain,
            expires_in=expires_in,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        row = await self._refresh_tokens.get_valid_by_token(refresh_token)
        if row is None:
            raise ValueError("invalid_refresh_token")
        user = await self._users.get_by_id(row.user_id)
        if user is None or not user.active:
            raise ValueError("invalid_refresh_token")

        now = datetime.now(UTC)
        await self._refresh_tokens.revoke(row, now)

        access_token, expires_in = create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            role=user.role,
            settings=self._settings,
        )
        new_refresh_plain = generate_opaque_refresh_token()
        expires_at = now + timedelta(days=self._settings.jwt_refresh_token_expire_days)
        await self._refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=RefreshTokenRepository.store_hash(new_refresh_plain),
                expires_at=expires_at,
            )
        )
        await self._session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_plain,
            expires_in=expires_in,
        )

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile | None:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.active:
            return None
        return UserProfile(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role,  # type: ignore[arg-type]
            organization_id=str(user.organization_id),
            team_ids=[],
        )

    @staticmethod
    def user_to_authenticated(user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            display_name=user.display_name,
        )

    @staticmethod
    def normalize_login_email(email: str) -> str:
        return normalize_email(email)

    @staticmethod
    def hash_user_password(password: str) -> str:
        return hash_password(password)
