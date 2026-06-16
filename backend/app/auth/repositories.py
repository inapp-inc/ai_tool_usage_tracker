"""Auth data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_refresh_token
from app.models.auth import Organization, RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        result = await self._session.execute(
            select(User).where(User.email == normalized)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create(
        self,
        *,
        organization_id: UUID,
        email: str,
        password_hash: str,
        display_name: str | None,
        role: str,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            active=True,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(UTC)
        await self._session.flush()


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count(self) -> int:
        result = await self._session.execute(select(Organization))
        return len(result.scalars().all())

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
