"""Tests for threshold service validation."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.thresholds.schemas import ThresholdCreateRequest
from app.thresholds.service import ThresholdService


def test_validate_limit_rejects_invalid_budget_percent() -> None:
    with pytest.raises(HTTPException) as exc:
        ThresholdService._validate_limit("package_utilization_pct", Decimal("150"))
    assert exc.value.status_code == 400


def test_threshold_create_request_accepts_organization_scope() -> None:
    body = ThresholdCreateRequest.model_validate(
        {
            "name": "Org cap",
            "threshold_type": "token_count",
            "scope": "organization",
            "limit_value": 1000,
            "severity": "warning",
        }
    )
    assert body.scope == "organization"
    assert body.team_id is None
