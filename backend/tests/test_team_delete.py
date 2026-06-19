"""Tests for team deletion helpers."""

from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.reporting import ReportJob
from app.teams.deletion import remove_team_from_report_jobs


@pytest.mark.asyncio
async def test_remove_team_from_report_jobs() -> None:
    org_id = uuid4()
    team_id = uuid4()
    other_team_id = uuid4()

    job = ReportJob(
        id=uuid4(),
        organization_id=org_id,
        created_by=uuid4(),
        name="Monthly",
        report_type="usage",
        format="csv",
        schedule="once",
        status="completed",
        period_from=MagicMock(),
        period_to=MagicMock(),
        team_ids=[str(team_id), str(other_team_id)],
    )

    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [job]
    session.execute = AsyncMock(return_value=result)

    updated = await remove_team_from_report_jobs(
        session,
        organization_id=org_id,
        team_id=team_id,
    )

    assert updated == 1
    assert job.team_ids == [str(other_team_id)]
