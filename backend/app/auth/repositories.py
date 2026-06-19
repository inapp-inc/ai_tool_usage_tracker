"""Auth data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_refresh_token
from app.models.auth import Organization, RefreshToken, User
from app.models.roles import Role


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.role_ref))
            .where(User.email == normalized)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(User)
            .options(selectinload(User.role_ref))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())

    async def get_super_admin(self) -> User | None:
        result = await self._session.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .options(selectinload(User.role_ref))
            .where(Role.name == "super_admin")
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        email: str,
        password_hash: str,
        display_name: str | None,
        role: str,
        role_id: UUID | None = None,
    ) -> User:
        resolved_role_id = role_id
        if resolved_role_id is None:
            role_row = await self._session.execute(
                select(Role.id).where(
                    Role.organization_id == organization_id,
                    Role.name == role,
                )
            )
            resolved_role_id = role_row.scalar_one_or_none()
        if resolved_role_id is None:
            raise ValueError(f"No role_id found for role '{role}' in organization {organization_id}")

        user = User(
            organization_id=organization_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            display_name=display_name,
            role_id=resolved_role_id,
            active=True,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)
        await self._session.flush()

    async def update_credentials(
        self,
        user: User,
        *,
        email: str,
        password_hash: str,
        display_name: str | None = None,
    ) -> None:
        user.email = email.strip().lower()
        user.password_hash = password_hash
        if display_name is not None:
            user.display_name = display_name
        await self._session.flush()


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Organization))
        return int(result.scalar_one())

    async def get_first(self) -> Organization | None:
        result = await self._session.execute(select(Organization).limit(1))
        return result.scalar_one_or_none()

    async def create(self, *, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self._session.add(org)
        await self._session.flush()
        return org


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: UUID, token: str, expires_at: datetime) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(token),
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_valid_by_token(self, token: str) -> RefreshToken | None:
        token_hash = hash_refresh_token(token)
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        record = result.scalar_one_or_none()
        if record is None or record.revoked_at is not None:
            return None
        if record.expires_at <= datetime.now(UTC):
            return None
        return record

    async def revoke(self, record: RefreshToken) -> None:
        record.revoked_at = datetime.now(UTC)
        await self._session.flush()
