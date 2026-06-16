"""Pydantic schemas for role permissions API."""

from __future__ import annotations

from pydantic import BaseModel


class PageAccess(BaseModel):
    read: bool = False
    write: bool = False


class RolePermissionMatrix(BaseModel):
    """Permissions for the three configurable roles. SuperAdmin is not included."""
    team_admin:     dict[str, PageAccess] = {}
    finance_viewer: dict[str, PageAccess] = {}
    auditor:        dict[str, PageAccess] = {}


class PermissionsResponse(BaseModel):
    permissions: RolePermissionMatrix
    pages: list[str]
    roles: list[str]


class UpdatePermissionsRequest(BaseModel):
    permissions: RolePermissionMatrix


class MyAccessResponse(BaseModel):
    role: str
    access: dict[str, PageAccess]
