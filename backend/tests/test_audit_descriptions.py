"""Audit description helper tests."""

from app.audit.descriptions import build_description, format_role_label


def test_build_description_login() -> None:
    assert build_description("auth.login") == "Signed in to the platform"


def test_build_description_team_create() -> None:
    assert build_description("team.create", resource_name="Engineering") == (
        "Created team Engineering"
    )


def test_format_role_label() -> None:
    assert format_role_label("super_admin") == "Super Admin"
