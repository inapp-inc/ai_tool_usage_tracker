"""Tests for Copilot organization_id URL binding."""

from datetime import UTC, datetime

from app.integration.placeholders import apply_placeholders, build_context
from app.settings.builtin_catalog import COPILOT_INTEGRATION_CONFIG
from app.tools.pricing import organization_id_from_pricing, vendor_requires_organization_id


def test_vendor_requires_organization_id_for_copilot() -> None:
    assert vendor_requires_organization_id("copilot") is True
    assert vendor_requires_organization_id("openai") is False


def test_organization_id_from_pricing() -> None:
    assert organization_id_from_pricing({"organization_id": "my-org"}) == "my-org"
    assert organization_id_from_pricing({}) is None


def test_copilot_url_placeholder_resolves() -> None:
    since = datetime(2026, 6, 1, tzinfo=UTC)
    until = datetime(2026, 6, 2, tzinfo=UTC)
    context = build_context(
        api_endpoint="https://api.github.com",
        since=since,
        until=until,
        pricing_config={"organization_id": "acme-corp"},
    )
    url = apply_placeholders(COPILOT_INTEGRATION_CONFIG["usage"]["url"], context)
    assert url == "https://api.github.com/orgs/acme-corp/copilot/billing/seats"
    assert "{" not in url
