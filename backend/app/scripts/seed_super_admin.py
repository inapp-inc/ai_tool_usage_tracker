"""Create or sync the bootstrap super admin from SUPER_ADMIN_* env vars.

Usage (inside api container):
  python -m app.scripts.seed_super_admin
"""

from __future__ import annotations

import asyncio
import sys

from app.auth.service import seed_super_admin_if_empty, sync_super_admin_credentials
from app.config import get_settings
from app.db.session import get_session_factory


async def main() -> int:
    settings = get_settings()
    session_factory = get_session_factory(settings)
    async with session_factory() as session:
        created = await seed_super_admin_if_empty(session, settings)
        synced = False
        if not created and settings.sync_super_admin_credentials:
            synced = await sync_super_admin_credentials(session, settings)

    if created:
        print(
            f"Created super admin: {settings.super_admin_email} "
            "(password from SUPER_ADMIN_PASSWORD)"
        )
        return 0

    if synced:
        print(
            f"Updated super admin credentials: {settings.super_admin_email} "
            "(password from SUPER_ADMIN_PASSWORD)"
        )
        return 0

    print("No changes — users already exist and sync is disabled or no super admin found.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
