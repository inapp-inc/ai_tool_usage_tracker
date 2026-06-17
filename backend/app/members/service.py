"""Unified org member listing — invited platform users and tool token emails."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.members.schemas import (
    MemberListResponse,
    MemberResponse,
    MemberTeamSummary,
    MembersView,
    PaginationMeta,
)
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository
from app.teams.tool_members import fetch_tool_members_for_team
from app.teams.upload_members import fetch_upload_members_for_team
from app.users.repository import UserAdminRepository


class MembersService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserAdminRepository(session)
        self._memberships = TeamMembershipRepository(session)
        self._teams = TeamRepository(session)

    async def list_members(
        self,
        organization_id: UUID,
        *,
        view: MembersView = "all",
        managed_team_ids: list[UUID] | None = None,
    ) -> MemberListResponse:
        users = await self._users.list_by_organization(organization_id)
        summaries = await self._memberships.list_team_summaries_for_users(
            organization_id,
            [row.id for row in users],
        )

        managed_set = set(managed_team_ids) if managed_team_ids else None

        platform_emails: set[str] = set()
        data: list[MemberResponse] = []

        for user in users:
            team_rows = summaries.get(user.id, [])
            if managed_set is not None:
                user_team_ids = {team.id for team, _ in team_rows}
                if not user_team_ids.intersection(managed_set):
                    continue
            platform_emails.add(user.email.lower())
            data.append(
                MemberResponse(
                    user_id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    role=user.role,  # type: ignore[arg-type]
                    active=user.active,
                    last_login_at=user.last_login_at,
                    created_at=user.created_at,
                    source="platform",
                    teams=[
                        MemberTeamSummary(
                            id=team.id,
                            name=team.name,
                            joined_at=joined_at,
                        )
                        for team, joined_at in team_rows
                    ],
                )
            )

        if view == "all":
            all_teams = await self._teams.list_by_organization(organization_id, active=None)
            teams = (
                [t for t in all_teams if t.id in managed_set]
                if managed_set is not None
                else all_teams
            )
            tool_by_email: dict[str, MemberResponse] = {}
            upload_by_email: dict[str, MemberResponse] = {}

            for team in teams:
                tool_entries = await fetch_tool_members_for_team(self._session, team)
                for entry in tool_entries:
                    email_lower = entry.email.lower()
                    if email_lower in platform_emails:
                        continue

                    existing = tool_by_email.get(email_lower)
                    if existing is not None:
                        if not any(summary.id == team.id for summary in existing.teams):
                            existing.teams.append(
                                MemberTeamSummary(id=team.id, name=team.name)
                            )
                        continue

                    tool_by_email[email_lower] = MemberResponse(
                        user_id=None,
                        email=entry.email,
                        display_name=entry.name,
                        active=True,
                        source="tool",
                        tool_id=entry.tool_id,
                        tool_name=entry.tool_name,
                        teams=[MemberTeamSummary(id=team.id, name=team.name)],
                    )

                upload_entries = await fetch_upload_members_for_team(
                    self._session,
                    organization_id,
                    team,
                )
                for entry in upload_entries:
                    email_lower = entry.email.lower()
                    if email_lower in platform_emails or email_lower in tool_by_email:
                        continue

                    existing = upload_by_email.get(email_lower)
                    if existing is not None:
                        if not any(summary.id == team.id for summary in existing.teams):
                            existing.teams.append(
                                MemberTeamSummary(id=team.id, name=team.name)
                            )
                        continue

                    upload_by_email[email_lower] = MemberResponse(
                        user_id=None,
                        email=entry.email,
                        display_name=entry.name,
                        active=True,
                        source="upload",
                        teams=[MemberTeamSummary(id=team.id, name=team.name)],
                    )

            data.extend(tool_by_email.values())
            data.extend(upload_by_email.values())

        data.sort(key=lambda row: row.email.lower())
        return MemberListResponse(
            data=data,
            meta=PaginationMeta(has_more=False),
        )
