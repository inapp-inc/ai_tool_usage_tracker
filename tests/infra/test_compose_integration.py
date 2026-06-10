"""Optional integration smoke tests against running Docker Compose stack."""

import json
import os
import urllib.error
import urllib.request

import pytest

API_HEALTH_URL = os.getenv("API_HEALTH_URL", "http://localhost:8000/health")


@pytest.mark.integration
def test_api_health_reports_postgres_and_redis_ok() -> None:
    """TASK-INF-001: API connects to postgres and redis via service hostnames."""
    try:
        with urllib.request.urlopen(API_HEALTH_URL, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"Compose stack not running: {exc}")

    assert payload["status"] == "ok"
    assert payload["database"] == "ok"
    assert payload["redis"] == "ok"
