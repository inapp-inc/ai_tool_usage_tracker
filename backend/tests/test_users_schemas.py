"""Tests for members API adapter mapping."""

from app.users.schemas import UserCreateRequest


def test_user_create_request_accepts_team_ids() -> None:
    body = UserCreateRequest.model_validate(
        {
            "email": "dev@acme.example",
            "display_name": "Dev User",
            "role": "team_member",
            "team_ids": [],
        }
    )
    assert body.email == "dev@acme.example"
    assert body.role == "team_member"
