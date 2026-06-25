"""Compose configuration tests for foundation hardening (TASK-INF-001)."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def _load_compose() -> dict:
    return yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))


def test_api_startup_runs_alembic_upgrade() -> None:
    compose = _load_compose()
    api = compose["services"]["api"]
    command = api["command"]
    if isinstance(command, str):
        command_str = command
    else:
        command_str = " ".join(command)
    assert "alembic upgrade head" in command_str
    assert "uvicorn" in command_str


def test_api_healthcheck_uses_v1_path() -> None:
    compose = _load_compose()
    healthcheck = compose["services"]["api"]["healthcheck"]
    test_cmd = " ".join(healthcheck["test"])
    assert "/api/v1/health" in test_cmd


def test_frontend_production_service() -> None:
    compose = _load_compose()
    frontend = compose["services"]["frontend"]
    assert frontend.get("profiles") == ["prod"]
    assert frontend.get("build") is not None
    assert "4501" in str(frontend.get("ports", []))


def test_frontend_dev_dev_profile_only() -> None:
    compose = _load_compose()
    frontend_dev = compose["services"]["frontend-dev"]
    assert frontend_dev.get("profiles") == ["dev"]
    assert "5173" in str(frontend_dev.get("ports", []))


def test_prod_profile_excludes_frontend_dev() -> None:
    """Production (--profile prod) must not start the Vite dev container."""
    import subprocess

    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "-f",
            str(REPO_ROOT / "docker-compose.prod.yml"),
            "--profile",
            "prod",
            "config",
            "--services",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    services = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert "frontend-dev" not in services
    assert "frontend" in services
    assert "api" in services
    assert "postgres" in services


def test_postgres_default_host_port_is_5433() -> None:
    compose = _load_compose()
    ports = compose["services"]["postgres"]["ports"]
    assert "5433" in str(ports)
