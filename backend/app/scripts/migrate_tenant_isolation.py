"""One-shot tenant isolation migration for existing databases."""

import asyncio

from app.db.session import get_session_factory
from app.organizations.service import ensure_platform_organization, ensure_tenant_isolation


async def main() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_platform_organization(session)
        moved = await ensure_tenant_isolation(session)
        await session.commit()
        print(f"Tenant isolation complete. Relocated {moved} organization admin(s).")


if __name__ == "__main__":
    asyncio.run(main())
