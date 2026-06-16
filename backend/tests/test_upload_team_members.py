"""Tests for upload-sourced team members."""

from uuid import uuid4

from app.teams.upload_members import UploadMemberEntry, fetch_upload_members_for_team


class _FakeScalars:
    def __init__(self, rows: list[tuple[str | None]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[str | None]]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[tuple[str | None]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[str | None]]:
        return self._rows


class _FakeSession:
    def __init__(self, rows: list[tuple[str | None]]) -> None:
        self._rows = rows

    async def execute(self, _query):  # noqa: ANN001
        return _FakeResult(self._rows)


class _FakeTeam:
    id = uuid4()


async def test_fetch_upload_members_deduplicates_emails() -> None:
    team = _FakeTeam()
    session = _FakeSession(
        [
            ("dev@acme.example",),
            ("dev@acme.example",),
            ("other@acme.example",),
        ]
    )

    entries = await fetch_upload_members_for_team(session, uuid4(), team)

    assert entries == [
        UploadMemberEntry(email="dev@acme.example"),
        UploadMemberEntry(email="other@acme.example"),
    ]
