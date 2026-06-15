"""Development seed for default organization and Super Admin."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories.organization import OrganizationRepository
from app.auth.repositories.user import UserRepository
from app.auth.service import AuthService
from app.config import get_settings
from app.db.session import get_session_factory
from app.models.auth import Organization, User


async def seed_dev_admin() -> None:
    """Create default org and super admin when auth tables are empty."""
    settings = get_settings()
    if settings.environment != "development":
        print("Skipping dev seed: ENVIRONMENT is not development")
        return

    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        user_repo = UserRepository(session)
        if await user_repo.count() > 0:
            print("Skipping dev seed: users already exist")
            return

        org_repo = OrganizationRepository(session)
        organization = Organization(
            id=uuid.uuid4(),
            name="Default Organization",
            slug="default",
            timezone="UTC",
        )
        await org_repo.add(organization)

        user = User(
            id=uuid.uuid4(),
            organization_id=organization.id,
            email=AuthService.normalize_login_email(settings.dev_super_admin_email),
            password_hash=AuthService.hash_user_password(settings.dev_super_admin_password),
            display_name="Platform Admin",
            role="super_admin",
            active=True,
        )
        await user_repo.add(user)

        from app.models.admin import Team

        team = Team(
            id=uuid.uuid4(),
            organization_id=organization.id,
            name="Engineering",
            description="Default engineering team for development.",
            settings={"toolIds": [], "tokenBudget": None, "costBudget": None},
        )
        session.add(team)

        from app.admin.providers.defaults import DEFAULT_PROVIDERS
        from app.models.admin import Provider

        for row in DEFAULT_PROVIDERS:
            session.add(
                Provider(
                    id=uuid.uuid4(),
                    organization_id=organization.id,
                    slug=str(row["slug"]),
                    name=str(row["name"]),
                    usage_api_url=str(row["usage_api_url"]),
                    description=str(row["description"]) if row.get("description") else None,
                    is_system=bool(row.get("is_system", False)),
                    active=True,
                )
            )

        await session.commit()
        print(f"Seeded super admin: {user.email}")
        print("Seeded default team: Engineering")


def main() -> None:
    asyncio.run(seed_dev_admin())


if __name__ == "__main__":
    main()
