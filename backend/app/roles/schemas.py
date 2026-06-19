"""Pydantic schemas for Roles API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    is_system: bool
    created_at: datetime


class RoleListResponse(BaseModel):
    data: list[RoleResponse]


class CreateRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=2000)


class UpdateRoleRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=2000)


class PermissionMatrixItem(BaseModel):
    resource: str
    can_read: bool
    can_write: bool
    team_scoped: bool


class PermissionMatrixResponse(BaseModel):
    data: list[PermissionMatrixItem]


class ReplacePermissionsRequest(BaseModel):
    permissions: list[PermissionMatrixItem]
