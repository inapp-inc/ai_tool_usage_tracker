"""Tests for Problem Details JSON responses."""

from decimal import Decimal

from app.core.exceptions import problem_response


def test_problem_response_serializes_decimal_in_extra() -> None:
    response = problem_response(
        status=422,
        title="Validation error",
        detail="One or more fields failed validation.",
        type_suffix="validation-error",
        extra={
            "errors": [
                {
                    "type": "less_than_equal",
                    "loc": ("body", "alert_threshold"),
                    "msg": "Input should be less than or equal to 100",
                    "input": Decimal("150"),
                }
            ]
        },
    )
    assert response.status_code == 422
    body = response.body.decode()
    assert "150" in body
    assert "Decimal" not in body
