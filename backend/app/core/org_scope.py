"""Resolve which organization(s) a request operates on."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.repositories import OrganizationRepository
from app.db.session import get_session
from app.models.auth import Organization, User
from app.organizations.constants import PLATFORM_ORG_SLUGS
from app.organizations.service import is_platform_organization


@dataclass(frozen=True)
class OperatingOrgScope:
    """Organization context for list/mutate operations."""

    user: User
    organization_id: UUID | None
    single_org_id: UUID | None

    @property
    def is_super_admin(self) -> bool:
        return self.user.role_name == "super_admin"

    def require_single_org(self) -> UUID:
        if self.single_org_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Select a customer organization first.",
            )
        return self.single_org_id


def require_operating_organization_id(scope: OperatingOrgScope) -> UUID:
    """Tenant org for reads/writes; super admin must have selected a customer org."""
    return scope.require_single_org()


async def list_tenant_organizations(session: AsyncSession) -> list[Organization]:
    result = await session.execute(
        select(Organization)
        .where(Organization.slug.notin_(tuple(PLATFORM_ORG_SLUGS)))
        .order_by(Organization.name.asc())
    )
    return list(result.scalars().all())


async def list_tenant_organization_ids(session: AsyncSession) -> list[UUID]:
    return [org.id for org in await list_tenant_organizations(session)]


async def organization_ids_for_scope(
    session: AsyncSession,
    scope: OperatingOrgScope,
) -> list[UUID]:
    if scope.is_super_admin:
        if scope.single_org_id is not None:
            return [scope.single_org_id]
        return await list_tenant_organization_ids(session)
    return [scope.require_single_org()]


async def get_operating_org_scope(
    organization_id: UUID | None = Query(default=None, alias="organization_id"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OperatingOrgScope:
    if current_user.role_name != "super_admin":
        if organization_id is not None and organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access another organization.",
            )
        return OperatingOrgScope(
            user=current_user,
            organization_id=current_user.organization_id,
            single_org_id=current_user.organization_id,
        )

    if organization_id is not None:
        org_repo = OrganizationRepository(session)
        org = await org_repo.get_by_id(organization_id)
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )
        return OperatingOrgScope(
            user=current_user,
            organization_id=organization_id,
            single_org_id=organization_id,
        )

    return OperatingOrgScope(
        user=current_user,
        organization_id=None,
        single_org_id=None,
    )


async def resolve_target_organization_id(
    scope: OperatingOrgScope,
    session: AsyncSession,
    *,
    body_organization_id: UUID | None = None,
) -> UUID:
    """Pick org for create/invite — super admin may pass body or scope org."""
    if not scope.is_super_admin:
        return scope.require_single_org()

    if body_organization_id is not None:
        org_repo = OrganizationRepository(session)
        org = await org_repo.get_by_id(body_organization_id)
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )
        if is_platform_organization(org):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Select a customer organization for this member.",
            )
        return org.id

    org_id = scope.single_org_id
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Select a customer organization before inviting members.",
        )
    org_repo = OrganizationRepository(session)
    org = await org_repo.get_by_id(org_id)
    if org is not None and is_platform_organization(org):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Select a customer organization before inviting members.",
        )
    return org_id


async def resolve_user_create_organization(
    scope: OperatingOrgScope,
    session: AsyncSession,
    *,
    body_organization_id: UUID | None = None,
    organization_name: str | None = None,
    role_name: str | None = None,
) -> tuple[UUID, bool]:
    """Resolve target org for POST /users. Returns (org_id, org_was_created)."""
    from app.organizations.service import OrganizationService

    if not scope.is_super_admin:
        org_id = await resolve_target_organization_id(
            scope,
            session,
            body_organization_id=body_organization_id,
        )
        return org_id, False

    cleaned_name = (organization_name or "").strip()
    if cleaned_name and role_name == "org_admin":
        org_service = OrganizationService(session)
        org, created = await org_service.find_or_create_tenant_by_name(cleaned_name)
        return org.id, created

    if cleaned_name and role_name != "org_admin":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_name is only used when inviting an Organization Admin.",
        )

    org_id = await resolve_target_organization_id(
        scope,
        session,
        body_organization_id=body_organization_id,
    )
    return org_id, False
