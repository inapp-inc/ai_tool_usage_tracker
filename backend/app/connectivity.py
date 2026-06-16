"""Connectivity checks for PostgreSQL."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.db.session import get_engine


@dataclass(frozen=True)
class ConnectivityStatus:
    """Result of dependency connectivity checks."""

    database: str

    @property
    def is_healthy(self) -> bool:
        return self.database == "ok"


async def check_postgres(engine: AsyncEngine) -> str:
    """Verify PostgreSQL connectivity."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def verify_connectivity(settings: Settings) -> ConnectivityStatus:
    """Check PostgreSQL using configured service hostname."""
    engine = get_engine(settings)
    database_status = await check_postgres(engine)
    return ConnectivityStatus(database=database_status)
