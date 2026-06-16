"""Members discovered from completed file uploads assigned to a team."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Team
from app.models.ingestion import ParsedRow, Upload


@dataclass(frozen=True)
class UploadMemberEntry:
    email: str
    name: str | None = None


async def fetch_upload_members_for_team(
    session: AsyncSession,
    organization_id: UUID,
    team: Team,
) -> list[UploadMemberEntry]:
    result = await session.execute(
        select(ParsedRow.user_email)
        .join(Upload, Upload.id == ParsedRow.upload_id)
        .where(
            Upload.organization_id == organization_id,
            Upload.team_id == team.id,
            Upload.status == "completed",
            Upload.deleted_at.is_(None),
            ParsedRow.user_email.is_not(None),
        )
        .distinct()
    )

    entries: list[UploadMemberEntry] = []
    seen: set[str] = set()
    for (email_raw,) in result.all():
        if not email_raw:
            continue
        email = str(email_raw).strip()
        if not email:
            continue
        normalized = email.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        entries.append(UploadMemberEntry(email=email))

    entries.sort(key=lambda row: row.email.lower())
    return entries
