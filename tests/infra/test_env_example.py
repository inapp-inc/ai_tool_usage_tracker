"""Tests for .env.example (NFR-SEC-008, TASK-INF-001)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = REPO_ROOT / ".env.example"

REQUIRED_KEYS = {
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "STORAGE_BACKEND",
    "LOCAL_STORAGE_ROOT",
}


def _parse_env_example() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def test_env_example_exists() -> None:
    """Environment template must be present for local setup."""
    assert ENV_EXAMPLE.is_file()


def test_env_example_documents_required_variables() -> None:
    """Required variables are documented without production secrets."""
    values = _parse_env_example()
    assert REQUIRED_KEYS.issubset(values.keys())


def test_env_example_uses_compose_hostnames() -> None:
    """In-container URLs reference Docker Compose service names."""
    values = _parse_env_example()
    assert "@postgres:5432/" in values["DATABASE_URL"]
    assert values["REDIS_URL"].startswith("redis://redis:")


def test_env_example_uses_dev_placeholders_only() -> None:
    """Template values are placeholders, not real credentials."""
    values = _parse_env_example()
    assert "change_me" in values["POSTGRES_PASSWORD"]
    assert "change_me" in values["JWT_SECRET_KEY"]
