"""Development seed — creates one sample user for each non-superadmin role.

Run from the backend directory:
    python -m app.scripts.seed_dev_roles

Credentials created
-------------------
team_admin   teamadmin@acme.example   / DevPass123!   (added to Engineering team)
finance_viewer finance@acme.example   / DevPass123!
auditor      auditor@acme.example     / DevPass123!
team_member  member@acme.example      / DevPass123!   (added to Engineering team)

Safe to run multiple times — skips any email that already exists.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.auth.repositories.user import UserRepository
from app.auth.service import AuthService
from app.config import get_settings
from app.db.session import get_session_factory
from app.models.admin import Team, TeamMembership
from app.models.auth import Organization, User

DEV_PASSWORD = "DevPass123!"

ROLE_USERS = [
    {
        "email": "teamadmin@acme.example",
        "display_name": "Team Admin",
        "role": "team_admin",
        "add_to_team": True,
    },
    {
        "email": "finance@acme.example",
        "display_name": "Finance Viewer",
        "role": "finance_viewer",
        "add_to_team": False,
    },
    {
        "email": "auditor@acme.example",
        "display_name": "Auditor",
        "role": "auditor",
        "add_to_team": False,
    },
    {
        "email": "member@acme.example",
        "display_name": "Team Member",
        "role": "team_member",
        "add_to_team": True,
    },
]


async def seed_dev_roles() -> None:
    settings = get_settings()
    if settings.environment != "development":
        print("Skipping: ENVIRONMENT is not development")
        return

    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        # Find existing org
        org_result = await session.execute(
            select(Organization).where(Organization.slug == "default")
        )
        org: Organization | None = org_result.scalar_one_or_none()
        if org is None:
            print("No default org found — run seed_dev_admin first.")
            return

        # Find Engineering team
        team_result = await session.execute(
            select(Team).where(
                Team.organization_id == org.id,
                Team.name == "Engineering",
            )
        )
        team: Team | None = team_result.scalar_one_or_none()
        if team is None:
            print("Engineering team not found — run seed_dev_admin first.")
            return

        user_repo = UserRepository(session)

        for spec in ROLE_USERS:
            normalized_email = AuthService.normalize_login_email(spec["email"])
            existing = await user_repo.get_by_email(normalized_email)
            if existing is not None:
                print(f"Skipping {spec['email']} — already exists")
                continue

            user = User(
                id=uuid.uuid4(),
                organization_id=org.id,
                email=normalized_email,
                password_hash=AuthService.hash_user_password(DEV_PASSWORD),
                display_name=spec["display_name"],
                role=spec["role"],
                active=True,
            )
            await user_repo.add(user)

            if spec["add_to_team"] and team is not None:
                session.add(
                    TeamMembership(
                        id=uuid.uuid4(),
                        organization_id=org.id,
                        team_id=team.id,
                        user_id=user.id,
                    )
                )

            print(f"Created {spec['role']}: {spec['email']}")

        await session.commit()
        print("\nDone. All new users have password: DevPass123!")


def main() -> None:
    asyncio.run(seed_dev_roles())


if __name__ == "__main__":
    main()
