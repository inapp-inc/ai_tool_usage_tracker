"""Tenant organization provisioning and listing."""

import re
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.repositories import OrganizationRepository, UserRepository
from app.auth.service import _ensure_system_roles
from app.core.security import hash_password
from app.models.admin import Team, TeamMembership
from app.models.auth import Organization, User
from app.models.roles import Role
from app.organizations.constants import PLATFORM_ORG_SLUGS
from app.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationCreateResponse,
    OrganizationInitialMemberRequest,
    OrganizationListResponse,
    OrganizationResponse,
)
from app.tools.builtin_seed import sync_org_builtin_catalogue_tools


def _normalize_slug(raw: str) -> str:
    slug = raw.strip().lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        msg = "Organization slug is required."
        raise ValueError(msg)
    return slug


def is_platform_organization(org: Organization) -> bool:
    return org.slug in PLATFORM_ORG_SLUGS


async def assert_tenant_organization(session: AsyncSession, organization_id: UUID) -> Organization:
    org_repo = OrganizationRepository(session)
    org = await org_repo.get_by_id(organization_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if is_platform_organization(org):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tenant users must belong to a customer organization, not the platform organization.",
        )
    return org


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._orgs = OrganizationRepository(session)
        self._users = UserRepository(session)

    async def list_organizations(self) -> OrganizationListResponse:
        rows = await self._orgs.list_all()
        return OrganizationListResponse(
            data=[OrganizationResponse.model_validate(row) for row in rows],
        )

    async def create_organization(
        self,
        body: OrganizationCreateRequest,
    ) -> OrganizationCreateResponse:
        name = body.name.strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Organization name is required.",
            )

        existing_by_name = await self._find_tenant_by_name(name)
        if existing_by_name is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An organization with this name already exists.",
            )

        slug = await self._allocate_unique_slug(name)
        org = await self._orgs.create(name=name, slug=slug)
        await _ensure_system_roles(self._session, org.id)
        await sync_org_builtin_catalogue_tools(self._session, org.id)

        initial_user_id: UUID | None = None
        initial_user_email: EmailStr | None = None

        if body.initial_member is not None:
            initial_user_id, initial_user_email = await self._create_initial_member(
                org,
                body.initial_member,
            )

        await self._session.commit()
        await self._session.refresh(org)

        return OrganizationCreateResponse(
            organization=OrganizationResponse.model_validate(org),
            initial_user_id=initial_user_id,
            initial_user_email=initial_user_email,
        )

    async def _create_initial_member(
        self,
        org: Organization,
        member: OrganizationInitialMemberRequest,
    ) -> tuple[UUID, EmailStr]:
        existing_user = await self._users.get_by_email(member.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        role_row = await self._session.execute(
            select(Role.id).where(
                Role.organization_id == org.id,
                Role.name == member.role_name,
            )
        )
        role_id = role_row.scalar_one_or_none()
        if role_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Organization roles were not seeded.",
            )

        display_name = (member.display_name or member.email.split("@", 1)[0]).strip()
        user = await self._users.create(
            organization_id=org.id,
            email=member.email,
            password_hash=hash_password(member.password),
            display_name=display_name,
            role=member.role_name,
            role_id=role_id,
        )

        if member.role_name not in {"org_admin", "finance_viewer", "auditor"}:
            default_team = Team(
                organization_id=org.id,
                name=f"{org.name} Team",
                active=True,
            )
            self._session.add(default_team)
            await self._session.flush()
            membership = TeamMembership(
                organization_id=org.id,
                team_id=default_team.id,
                user_id=user.id,
            )
            self._session.add(membership)

        return user.id, member.email

    async def find_or_create_tenant_by_name(self, name: str) -> tuple[Organization, bool]:
        """Find tenant by display name or create one with seeded roles and tools."""
        cleaned = name.strip()
        existing = await self._find_tenant_by_name(cleaned)
        if existing is not None:
            return existing, False

        slug = await self._allocate_unique_slug(cleaned)
        org = await self._orgs.create(name=cleaned, slug=slug)
        await _ensure_system_roles(self._session, org.id)
        await sync_org_builtin_catalogue_tools(self._session, org.id)
        return org, True

    async def _find_tenant_by_name(self, name: str) -> Organization | None:
        normalized = name.strip().lower()
        result = await self._session.execute(select(Organization))
        for org in result.scalars().all():
            if org.name.strip().lower() == normalized and not is_platform_organization(org):
                return org
        return None

    async def _allocate_unique_slug(self, name: str) -> str:
        base = _normalize_slug(name)
        if base in PLATFORM_ORG_SLUGS:
            base = f"{base}-org"
        slug = base
        suffix = 1
        while await self._orgs.get_by_slug(slug) is not None:
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug


async def ensure_platform_organization(session: AsyncSession) -> Organization | None:
    """Rename legacy default org to platform and return the platform org."""
    org_repo = OrganizationRepository(session)
    platform = await org_repo.get_by_slug("platform")
    if platform is not None:
        return platform

    legacy = await org_repo.get_by_slug("default")
    if legacy is not None:
        legacy.name = "Platform Administration"
        legacy.slug = "platform"
        await session.flush()
        return legacy

    first = await org_repo.get_first()
    if first is not None and first.slug not in PLATFORM_ORG_SLUGS:
        return None

    if first is not None:
        first.name = "Platform Administration"
        first.slug = "platform"
        await session.flush()
        return first

    return None


def _tenant_slug_for_user(user: User) -> str:
    local = user.email.split("@", 1)[0]
    return _normalize_slug(local)


async def ensure_tenant_isolation(session: AsyncSession) -> int:
    """Move org_admin users out of the platform org into dedicated tenant orgs.

    Returns the number of org_admin users relocated.
    """
    platform = await ensure_platform_organization(session)
    if platform is None:
        return 0

    result = await session.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(selectinload(User.role_ref))
        .where(
            User.organization_id == platform.id,
            Role.name == "org_admin",
        )
    )
    org_admins = list(result.scalars().unique().all())
    if not org_admins:
        return 0

    org_repo = OrganizationRepository(session)
    moved = 0

    for admin in org_admins:
        base_slug = _tenant_slug_for_user(admin)
        slug = base_slug
        suffix = 1
        while await org_repo.get_by_slug(slug) is not None:
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        display = (admin.display_name or admin.email.split("@", 1)[0]).strip()
        tenant = await org_repo.create(
            name=f"{display} Organization",
            slug=slug,
        )
        await _ensure_system_roles(session, tenant.id)
        await sync_org_builtin_catalogue_tools(session, tenant.id)

        role_row = await session.execute(
            select(Role.id).where(
                Role.organization_id == tenant.id,
                Role.name == "org_admin",
            )
        )
        role_id = role_row.scalar_one()

        admin.organization_id = tenant.id
        admin.role_id = role_id
        await session.execute(
            delete(TeamMembership).where(TeamMembership.user_id == admin.id)
        )
        moved += 1

    await session.flush()
    return moved


async def remove_platform_org_admin_role(session: AsyncSession) -> bool:
    """Remove org_admin role from the platform org when no users are assigned to it."""
    from app.models.roles import Role, RolePermission
    from sqlalchemy import delete, select

    platform = await ensure_platform_organization(session)
    if platform is None:
        return False

    role_row = await session.execute(
        select(Role.id).where(
            Role.organization_id == platform.id,
            Role.name == "org_admin",
        )
    )
    role_id = role_row.scalar_one_or_none()
    if role_id is None:
        return False

    assigned = await session.execute(
        select(User.id).where(User.role_id == role_id).limit(1)
    )
    if assigned.scalar_one_or_none() is not None:
        return False

    await session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    await session.execute(delete(Role).where(Role.id == role_id))
    await session.flush()
    return True
