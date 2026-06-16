"""Authentication service — login, refresh, profile."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories import OrganizationRepository, RefreshTokenRepository, UserRepository
from app.teams.membership_repository import TeamMembershipRepository
from app.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, UserProfile
from app.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)
from app.models.auth import User


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._users = UserRepository(session)
        self._memberships = TeamMembershipRepository(session)
        self._refresh_tokens = RefreshTokenRepository(session)

    async def login(self, body: LoginRequest) -> TokenResponse:
        user = await self._users.get_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
            )
        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive.",
            )

        await self._users.update_last_login(user)
        return await self._issue_tokens(user)

    async def refresh(self, body: RefreshRequest) -> TokenResponse:
        record = await self._refresh_tokens.get_valid_by_token(body.refresh_token)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        await self._refresh_tokens.revoke(record)
        return await self._issue_tokens(user)

    async def get_profile(self, user_id: UUID) -> UserProfile:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated.",
            )
        team_ids = await self._memberships.active_team_ids_for_user(user.id)
        return UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,  # type: ignore[arg-type]
            organization_id=user.organization_id,
            team_ids=team_ids,
        )

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token, expires_in = create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            role=user.role,
            email=user.email,
            settings=self._settings,
        )
        refresh_token = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.jwt_refresh_token_expire_days
        )
        await self._refresh_tokens.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )
        await self._session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )


async def seed_dev_admin(session: AsyncSession, settings: Settings | None = None) -> None:
    """Create default org + super admin when auth tables are empty (development only)."""
    cfg = settings or get_settings()
    if cfg.environment != "development":
        return

    org_repo = OrganizationRepository(session)
    if await org_repo.count() > 0:
        return

    org = await org_repo.create(name="Default Organization", slug="default")
    user_repo = UserRepository(session)
    await user_repo.create(
        organization_id=org.id,
        email=cfg.dev_super_admin_email,
        password_hash=hash_password(cfg.dev_super_admin_password),
        display_name="Super Admin",
        role="super_admin",
    )
    await session.commit()
