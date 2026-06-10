"""Project structure tests for bounded contexts (TASK-INF-002)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_APP = REPO_ROOT / "backend" / "app"

REQUIRED_PATHS = (
    "auth",
    "admin",
    "ingestion",
    "usage",
    "dashboard",
    "reporting",
    "notifications",
    "audit",
    "core",
    "db",
    "api/v1/router.py",
)


def test_bounded_context_packages_exist() -> None:
    for relative in REQUIRED_PATHS:
        path = BACKEND_APP / relative
        if relative.endswith(".py"):
            assert path.is_file(), f"Missing file: {relative}"
        else:
            assert path.is_dir(), f"Missing package: {relative}"
