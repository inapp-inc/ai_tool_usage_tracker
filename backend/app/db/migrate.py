"""Run Alembic migrations (sync subprocess — safe outside async event loop)."""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Apply all pending Alembic revisions via subprocess."""
    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    if not alembic_ini.is_file():
        msg = f"Alembic config not found: {alembic_ini}"
        raise FileNotFoundError(msg)

    logger.info("Running database migrations (alembic upgrade head)")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(backend_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        msg = f"Alembic upgrade failed: {detail}"
        raise RuntimeError(msg)
    logger.info("Database migrations complete")
