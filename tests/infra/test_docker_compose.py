"""Tests for docker-compose.yml (TASK-INF-001)."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"

REQUIRED_SERVICES = {"postgres", "redis", "api", "worker", "beat"}


def test_compose_file_exists() -> None:
    """Compose file must exist at repository root."""
    assert COMPOSE_FILE.is_file()


def test_compose_defines_required_services() -> None:
    """TASK-INF-001 requires postgres, redis, api, worker, and beat."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    services = set(compose.get("services", {}).keys())
    assert REQUIRED_SERVICES.issubset(services)


def test_postgres_uses_alpine_15_and_healthcheck() -> None:
    """PostgreSQL service matches database.md Docker deployment."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    postgres = compose["services"]["postgres"]

    assert postgres["image"] == "postgres:15-alpine"
    assert "postgres_data" in compose["volumes"]

    healthcheck = postgres["healthcheck"]
    test_command = " ".join(healthcheck["test"])
    assert "pg_isready" in test_command


def test_postgres_persists_named_volume() -> None:
    """postgres_data volume is mounted for PostgreSQL data."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    postgres = compose["services"]["postgres"]
    volume_mounts = postgres.get("volumes", [])
    assert any("postgres_data" in mount for mount in volume_mounts)


def test_api_depends_on_postgres_and_redis_health() -> None:
    """API waits for healthy postgres and redis before starting."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    depends_on = compose["services"]["api"]["depends_on"]

    assert depends_on["postgres"]["condition"] == "service_healthy"
    assert depends_on["redis"]["condition"] == "service_healthy"


def test_compose_defines_storage_volumes() -> None:
    """Local storage volumes for uploads, reports, and backups."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    volumes = compose.get("volumes", {})
    assert "storage_data" in volumes
    assert "backups_data" in volumes
    assert "redis_data" in volumes

    api = compose["services"]["api"]
    assert any("storage_data" in mount for mount in api.get("volumes", []))
    assert api["environment"].get("STORAGE_BACKEND") == "local"


def test_api_uses_compose_service_hostnames() -> None:
    """API receives POSTGRES_* vars; entrypoint builds DATABASE_URL with postgres host."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    environment = compose["services"]["api"]["environment"]

    assert environment["POSTGRES_USER"] == "${POSTGRES_USER:-aitracker}"
    assert environment["POSTGRES_PASSWORD"] == "${POSTGRES_PASSWORD}"
    assert environment["POSTGRES_DB"] == "${POSTGRES_DB:-aitracker}"

    entrypoint = REPO_ROOT / "backend" / "docker-entrypoint.sh"
    assert entrypoint.is_file()
    assert "@postgres:5432/" in entrypoint.read_text(encoding="utf-8")


def test_services_use_internal_network() -> None:
    """All stack services attach to the ai-tracker network."""
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    network_name = compose["networks"]["ai-tracker"]["name"]

    assert network_name == "ai-tracker-network"
    for service_name in REQUIRED_SERVICES:
        networks = compose["services"][service_name].get("networks", [])
        assert "ai-tracker" in networks
