"""Unit tests for tool request/response schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.tools.schemas import ToolCreateRequest, ToolResponse, normalize_api_endpoint


def test_custom_vendor_without_api_endpoint_returns_422() -> None:
    with pytest.raises(ValidationError, match="api_endpoint is required when vendor is custom"):
        ToolCreateRequest(
            name="Custom Tool",
            vendor="custom",
            pricing_model="flat_token",
            token_price=Decimal("0"),
        )


def test_api_endpoint_must_use_https() -> None:
    with pytest.raises(ValidationError, match="api_endpoint must start with https://"):
        ToolCreateRequest(
            name="Custom Tool",
            vendor="custom",
            api_endpoint="http://api.example.com/v1",
            pricing_model="flat_token",
            token_price=Decimal("0"),
        )


def test_create_request_ignores_legacy_api_key_field() -> None:
    body = ToolCreateRequest.model_validate(
        {
            "name": "OpenAI",
            "vendor": "openai",
            "pricing_model": "flat_token",
            "token_price": "0",
            "api_key": "sk-should-be-ignored",
        }
    )
    assert body.name == "OpenAI"
    assert "api_key" not in body.model_fields_set


def test_create_request_does_not_require_api_key() -> None:
    body = ToolCreateRequest(
        name="OpenAI",
        vendor="openai",
        pricing_model="flat_token",
        token_price=Decimal("0"),
    )
    assert body.vendor == "openai"


def test_custom_vendor_accepts_api_endpoint() -> None:
    body = ToolCreateRequest(
        name="Custom Tool",
        vendor="custom",
        api_endpoint="https://api.example.com/v1/chat/completions",
        pricing_model="flat_token",
        token_price=Decimal("0"),
    )
    assert body.api_endpoint == "https://api.example.com/v1/chat/completions"
    assert body.vendor == "custom"


def test_normalize_api_endpoint_trims_and_preserves_https() -> None:
    assert (
        normalize_api_endpoint("  https://api.example.com/v1  ")
        == "https://api.example.com/v1"
    )
    assert normalize_api_endpoint("") is None
    assert normalize_api_endpoint(None) is None


def test_tool_response_includes_api_endpoint() -> None:
    from datetime import UTC, datetime
    from uuid import uuid4

    now = datetime.now(UTC)
    response = ToolResponse(
        id=uuid4(),
        organization_id=uuid4(),
        name="Cursor",
        vendor="cursor",
        description="Team Cursor",
        api_endpoint="https://api.cursor.com/v1/me",
        pricing_model="flat_token",
        token_price=Decimal("0"),
        package_allowance=None,
        overage_price=None,
        pricing_config={},
        active=True,
        api_token_masked="",
        token_count=0,
        cost_total=Decimal("0"),
        balance_tokens=None,
        member_count=0,
        sync_status="inactive",
        last_sync_at=None,
        last_sync_error=None,
        created_at=now,
        updated_at=now,
    )
    assert response.api_endpoint == "https://api.cursor.com/v1/me"
