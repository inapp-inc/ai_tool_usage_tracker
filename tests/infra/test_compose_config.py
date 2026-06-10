"""Compose configuration tests for foundation hardening (TASK-INF-001)."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def _load_compose() -> dict:
    return yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))


def test_migrate_service_runs_alembic_upgrade() -> None:
    compose = _load_compose()
    migrate = compose["services"]["migrate"]
    assert migrate["command"] == ["alembic", "upgrade", "head"]
    assert migrate["restart"] == "no"


def test_api_healthcheck_uses_v1_path() -> None:
    compose = _load_compose()
    healthcheck = compose["services"]["api"]["healthcheck"]
    test_cmd = " ".join(healthcheck["test"])
    assert "/api/v1/health" in test_cmd


def test_frontend_dev_profile() -> None:
    compose = _load_compose()
    frontend = compose["services"]["frontend"]
    assert frontend.get("profiles") == ["dev"]
    assert "5173" in str(frontend.get("ports", []))


def test_worker_consumes_all_queues() -> None:
    compose = _load_compose()
    command = compose["services"]["worker"]["command"]
    command_str = " ".join(command)
    assert "ingestion,reports,alerts,email,maintenance" in command_str
