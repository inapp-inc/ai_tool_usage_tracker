"""Tests for tool service response mapping."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.tools.service import ToolService


@patch("app.tools.service.decrypt_token", return_value="")
def test_to_response_includes_api_endpoint(_decrypt: MagicMock) -> None:
    tool_id = uuid4()
    org_id = uuid4()
    now = datetime.now(UTC)

    tool = MagicMock()
    tool.id = tool_id
    tool.organization_id = org_id
    tool.name = "Custom API"
    tool.vendor = "custom"
    tool.description = "Custom integration"
    tool.api_endpoint = "https://api.example.com/v1/chat/completions"
    tool.pricing_model = "flat_token"
    tool.token_price = Decimal("0")
    tool.package_allowance = None
    tool.overage_price = None
    tool.pricing_config = {"provider_slug": "custom"}
    tool.active = True
    tool.api_token_ciphertext = "encrypted"
    tool.token_count = 0
    tool.cost_total = Decimal("0")
    tool.balance_tokens = None
    tool.member_count = 0
    tool.sync_status = "inactive"
    tool.last_sync_at = None
    tool.last_sync_error = None
    tool.created_at = now
    tool.updated_at = now

    response = ToolService._to_response(tool)

    assert response.api_endpoint == "https://api.example.com/v1/chat/completions"
    assert response.vendor == "custom"
    assert response.api_token_masked == ""
