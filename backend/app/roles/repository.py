"""Role data access."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.roles import Role, RolePermission, VALID_RESOURCES


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_org(self, organization_id: UUID) -> list[Role]:
        result = await self._session.execute(
            select(Role)
            .where(Role.organization_id == organization_id)
            .order_by(Role.is_system.desc(), Role.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, role_id: UUID, organization_id: UUID) -> Role | None:
        result = await self._session.execute(
            select(Role).where(
                Role.id == role_id,
                Role.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, organization_id: UUID, name: str) -> Role | None:
        result = await self._session.execute(
            select(Role).where(
                Role.organization_id == organization_id,
                Role.name == name.strip(),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        description: str | None,
        is_system: bool = False,
    ) -> Role:
        role = Role(
            organization_id=organization_id,
            name=name.strip(),
            description=description,
            is_system=is_system,
        )
        self._session.add(role)
        await self._session.flush()
        return role

    async def delete(self, role: Role) -> None:
        await self._session.delete(role)
        await self._session.flush()

    async def count_users_with_role(self, role_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(User)
            .where(User.role_id == role_id, User.active.is_(True))
        )
        return int(result.scalar_one())

    async def get_permissions(self, role_id: UUID) -> list[RolePermission]:
        result = await self._session.execute(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )
        return list(result.scalars().all())

    async def replace_permissions(
        self,
        role_id: UUID,
        items: list[dict],
    ) -> list[RolePermission]:
        existing = await self.get_permissions(role_id)
        for row in existing:
            await self._session.delete(row)
        await self._session.flush()

        created: list[RolePermission] = []
        for item in items:
            perm = RolePermission(
                role_id=role_id,
                resource=item["resource"],
                can_read=item["can_read"],
                can_write=item["can_write"],
                team_scoped=item["team_scoped"],
            )
            self._session.add(perm)
            created.append(perm)
        await self._session.flush()
        return created

    @staticmethod
    def build_full_matrix(stored: list[RolePermission]) -> list[dict]:
        by_resource = {row.resource: row for row in stored}
        matrix: list[dict] = []
        for resource in sorted(VALID_RESOURCES):
            row = by_resource.get(resource)
            if row is None:
                matrix.append(
                    {
                        "resource": resource,
                        "can_read": False,
                        "can_write": False,
                        "team_scoped": False,
                    }
                )
            else:
                matrix.append(
                    {
                        "resource": resource,
                        "can_read": row.can_read,
                        "can_write": row.can_write,
                        "team_scoped": row.team_scoped,
                    }
                )
        return matrix
