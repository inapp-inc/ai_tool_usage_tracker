"""Seed dev login accounts for each platform role.

Run from the project root:
    docker compose exec api python -m app.scripts.seed_dev_roles

Idempotent — skips any email that already exists.
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.security import hash_password
from app.models.auth import Organization, User
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository

DEV_PASSWORD = "DevPass123!"

ROLE_USERS = [
    {
        "email": "teamadmin@acme.example",
        "display_name": "Team Admin Dev",
        "role": "team_admin",
        "add_to_team": True,
    },
    {
        "email": "finance@acme.example",
        "display_name": "Finance Viewer Dev",
        "role": "finance_viewer",
        "add_to_team": False,
    },
    {
        "email": "auditor@acme.example",
        "display_name": "Auditor Dev",
        "role": "auditor",
        "add_to_team": False,
    },
    {
        "email": "member@acme.example",
        "display_name": "Team Member Dev",
        "role": "team_member",
        "add_to_team": True,
    },
]


async def seed(session: AsyncSession) -> None:
    result = await session.execute(select(Organization).limit(1))
    org = result.scalar_one_or_none()
    if org is None:
        print("ERROR: No organization found. Run the app once to auto-seed the super admin first.")
        return

    team_repo = TeamRepository(session)
    teams = await team_repo.list_by_organization(org.id, active=True)
    first_team = teams[0] if teams else None

    membership_repo = TeamMembershipRepository(session)

    for spec in ROLE_USERS:
        existing = await session.execute(
            select(User).where(
                User.organization_id == org.id,
                User.email == spec["email"],
            )
        )
        user = existing.scalar_one_or_none()

        if user is None:
            user = User(
                id=uuid.uuid4(),
                organization_id=org.id,
                email=spec["email"],
                display_name=spec["display_name"],
                password_hash=hash_password(DEV_PASSWORD),
                role=spec["role"],
                active=True,
            )
            session.add(user)
            await session.flush()
            print(f"  Created: {spec['email']} ({spec['role']})")
        else:
            print(f"  Skipped (exists): {spec['email']}")

        if spec["add_to_team"] and first_team is not None:
            try:
                await membership_repo.add(
                    organization_id=org.id,
                    team_id=first_team.id,
                    user_id=user.id,
                )
                print(f"    -> Added to team: {first_team.name}")
            except Exception:
                print("    -> Already in team or error — skipping membership.")

    await session.commit()
    print("Done.")


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[call-overload]

    async with async_session() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
