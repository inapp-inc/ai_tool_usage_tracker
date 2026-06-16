"""User admin data access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User


class UserAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(self, organization_id: UUID) -> list[User]:
        result = await self._session.execute(
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.email.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, user_id: UUID, organization_id: UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, organization_id: UUID, email: str) -> User | None:
        normalized = email.strip().lower()
        result = await self._session.execute(
            select(User).where(
                User.organization_id == organization_id,
                User.email == normalized,
            )
        )
        return result.scalar_one_or_none()
