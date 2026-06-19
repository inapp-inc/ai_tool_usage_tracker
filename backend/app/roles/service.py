"""Role management business logic."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionCache
from app.models.roles import VALID_RESOURCES
from app.roles.repository import RoleRepository
from app.roles.schemas import (
    CreateRoleRequest,
    PermissionMatrixItem,
    PermissionMatrixResponse,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
)


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._roles = RoleRepository(session)

    async def list_roles(self, organization_id: UUID) -> RoleListResponse:
        roles = await self._roles.list_by_org(organization_id)
        return RoleListResponse(data=[RoleResponse.model_validate(r) for r in roles])

    async def create_role(
        self,
        organization_id: UUID,
        body: CreateRoleRequest,
    ) -> RoleResponse:
        existing = await self._roles.get_by_name(organization_id, body.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A role with this name already exists.",
            )

        role = await self._roles.create(
            organization_id=organization_id,
            name=body.name,
            description=body.description,
            is_system=False,
        )

        await self._roles.replace_permissions(
            role.id,
            [
                {
                    "resource": resource,
                    "can_read": False,
                    "can_write": False,
                    "team_scoped": False,
                }
                for resource in sorted(VALID_RESOURCES)
            ],
        )
        await self._session.commit()
        await self._session.refresh(role)
        return RoleResponse.model_validate(role)

    async def update_role(
        self,
        organization_id: UUID,
        role_id: UUID,
        body: UpdateRoleRequest,
    ) -> RoleResponse:
        role = await self._require_role(organization_id, role_id)
        updates = body.model_fields_set

        if "name" in updates and body.name is not None and body.name.strip() != role.name:
            if role.is_system:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="System role names are immutable",
                )
            duplicate = await self._roles.get_by_name(organization_id, body.name)
            if duplicate is not None and duplicate.id != role.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A role with this name already exists.",
                )
            role.name = body.name.strip()

        if "description" in updates:
            role.description = body.description

        await self._session.commit()
        await self._session.refresh(role)
        return RoleResponse.model_validate(role)

    async def delete_role(self, organization_id: UUID, role_id: UUID) -> None:
        role = await self._require_role(organization_id, role_id)
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="System roles cannot be deleted",
            )

        active_users = await self._roles.count_users_with_role(role_id)
        if active_users > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role has active users assigned",
            )

        await self._roles.delete(role)
        await self._session.commit()

    async def get_permissions(
        self,
        organization_id: UUID,
        role_id: UUID,
    ) -> PermissionMatrixResponse:
        role = await self._require_role(organization_id, role_id)
        stored = await self._roles.get_permissions(role.id)
        matrix = RoleRepository.build_full_matrix(stored)
        return PermissionMatrixResponse(
            data=[PermissionMatrixItem.model_validate(item) for item in matrix]
        )

    async def replace_permissions(
        self,
        organization_id: UUID,
        role_id: UUID,
        items: list[PermissionMatrixItem],
    ) -> PermissionMatrixResponse:
        role = await self._require_role(organization_id, role_id)

        seen: set[str] = set()
        payload: list[dict] = []
        for item in items:
            if item.resource not in VALID_RESOURCES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid resource: {item.resource}",
                )
            if item.resource in seen:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Duplicate resource: {item.resource}",
                )
            seen.add(item.resource)
            can_read = item.can_read or item.can_write
            payload.append(
                {
                    "resource": item.resource,
                    "can_read": can_read,
                    "can_write": item.can_write,
                    "team_scoped": item.team_scoped,
                }
            )

        for resource in VALID_RESOURCES:
            if resource not in seen:
                payload.append(
                    {
                        "resource": resource,
                        "can_read": False,
                        "can_write": False,
                        "team_scoped": False,
                    }
                )

        await self._roles.replace_permissions(role.id, payload)
        await self._session.commit()
        PermissionCache.invalidate(role.id)
        return await self.get_permissions(organization_id, role_id)

    async def _require_role(self, organization_id: UUID, role_id: UUID):
        role = await self._roles.get_by_id(role_id, organization_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found.",
            )
        return role
