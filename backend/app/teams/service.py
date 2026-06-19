"""Team business logic."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.admin import Team
from app.models.auth import User
from app.teams.deletion import remove_team_from_report_jobs
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.metrics import TeamMetrics, TeamMetricsLoader
from app.teams.repository import TeamRepository
from app.teams.schemas import (
    PaginationMeta,
    TeamCreateRequest,
    TeamListResponse,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.teams.tool_members import fetch_tool_members_for_team
from app.teams.upload_members import fetch_upload_members_for_team
from app.users.repository import UserAdminRepository


class TeamService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)
        self._memberships = TeamMembershipRepository(session)
        self._users = UserAdminRepository(session)

    async def list_teams(
        self,
        user: User,
        *,
        active: bool | None = None,
    ) -> TeamListResponse:
        rows = await self._teams.list_by_organization(user.organization_id, active=active)
        metrics = await TeamMetricsLoader(self._session).load_for_teams(
            user.organization_id,
            rows,
        )
        responses: list[TeamResponse] = []
        for row in rows:
            member_count = len(await self._collect_team_members(user.organization_id, row))
            team_metrics = metrics.get(row.id)
            responses.append(
                self._to_response(
                    row,
                    member_count=member_count,
                    metrics=team_metrics,
                )
            )
        return TeamListResponse(
            data=responses,
            meta=PaginationMeta(has_more=False),
        )

    async def get_team(self, user: User, team_id: UUID) -> TeamResponse:
        team = await self._require_team(user.organization_id, team_id)
        member_count = len(await self._collect_team_members(user.organization_id, team))
        metrics_map = await TeamMetricsLoader(self._session).load_for_teams(
            user.organization_id,
            [team],
        )
        return self._to_response(
            team,
            member_count=member_count,
            metrics=metrics_map.get(team.id),
        )

    async def list_team_members(
        self,
        user: User,
        team_id: UUID,
    ) -> TeamMemberListResponse:
        team = await self._require_team(user.organization_id, team_id)
        data = await self._collect_team_members(user.organization_id, team)
        return TeamMemberListResponse(
            data=data,
            meta=PaginationMeta(has_more=False),
        )

    async def _collect_team_members(
        self,
        organization_id: UUID,
        team: Team,
    ) -> list[TeamMemberResponse]:
        memberships = await self._memberships.list_active_for_team(team.id)

        platform_emails: set[str] = set()
        data: list[TeamMemberResponse] = []

        for membership in memberships:
            member_user = await self._users.get_by_id(
                membership.user_id,
                organization_id,
            )
            if member_user is None:
                continue
            platform_emails.add(member_user.email.lower())
            data.append(
                TeamMemberResponse(
                    user_id=member_user.id,
                    email=member_user.email,
                    display_name=member_user.display_name,
                    joined_at=membership.joined_at,
                    source="platform",
                )
            )

        tool_entries = await fetch_tool_members_for_team(self._session, team)
        for entry in tool_entries:
            if entry.email.lower() in platform_emails:
                continue
            platform_emails.add(entry.email.lower())
            data.append(
                TeamMemberResponse(
                    user_id=None,
                    email=entry.email,
                    display_name=entry.name,
                    joined_at=None,
                    source="tool",
                    tool_id=entry.tool_id,
                    tool_name=entry.tool_name,
                )
            )

        upload_entries = await fetch_upload_members_for_team(
            self._session,
            organization_id,
            team,
        )
        for entry in upload_entries:
            if entry.email.lower() in platform_emails:
                continue
            platform_emails.add(entry.email.lower())
            data.append(
                TeamMemberResponse(
                    user_id=None,
                    email=entry.email,
                    display_name=entry.name,
                    joined_at=None,
                    source="upload",
                )
            )

        data.sort(key=lambda row: row.email.lower())
        return data

    async def add_team_member(
        self,
        user: User,
        team_id: UUID,
        member_user_id: UUID,
    ) -> TeamMemberResponse:
        team = await self._require_team(user.organization_id, team_id)
        member_user = await self._users.get_by_id(member_user_id, user.organization_id)
        if member_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        membership = await self._memberships.add(
            organization_id=user.organization_id,
            team_id=team.id,
            user_id=member_user.id,
        )
        await self._session.commit()
        return TeamMemberResponse(
            user_id=member_user.id,
            email=member_user.email,
            display_name=member_user.display_name,
            joined_at=membership.joined_at,
            source="platform",
        )

    async def remove_team_member(
        self,
        user: User,
        team_id: UUID,
        member_user_id: UUID,
    ) -> None:
        await self._require_team(user.organization_id, team_id)
        removed = await self._memberships.remove(team_id, member_user_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team member not found.",
            )
        await self._session.commit()

    async def create_team(self, user: User, body: TeamCreateRequest) -> TeamResponse:
        existing = await self._teams.get_by_name(user.organization_id, body.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A team with this name already exists in the organization.",
            )

        team = await self._teams.create(
            organization_id=user.organization_id,
            name=body.name,
            description=body.description,
            token_budget=body.token_budget,
            cost_budget=body.cost_budget,
            tool_ids=body.tool_ids,
        )
        await self._session.commit()
        await self._session.refresh(team)
        return self._to_response(team, member_count=0)

    async def update_team(
        self,
        user: User,
        team_id: UUID,
        body: TeamUpdateRequest,
    ) -> TeamResponse:
        team = await self._require_team(user.organization_id, team_id)
        updates = body.model_fields_set

        if "name" in updates and body.name is not None:
            if body.name.strip().lower() != team.name.lower():
                duplicate = await self._teams.get_by_name(user.organization_id, body.name)
                if duplicate is not None and duplicate.id != team.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A team with this name already exists in the organization.",
                    )
            team.name = body.name.strip()

        if "description" in updates:
            team.description = body.description.strip() if body.description else None

        if "active" in updates and body.active is not None:
            team.active = body.active

        if "token_budget" in updates:
            team.token_budget = body.token_budget

        if "cost_budget" in updates:
            team.cost_budget = body.cost_budget

        if "tool_ids" in updates and body.tool_ids is not None:
            team.tool_ids = list(body.tool_ids)
            flag_modified(team, "tool_ids")

        await self._session.commit()
        await self._session.refresh(team)
        member_count = len(await self._collect_team_members(user.organization_id, team))
        return self._to_response(team, member_count=member_count)

    async def delete_team(self, user: User, team_id: UUID) -> None:
        team = await self._require_team(user.organization_id, team_id)
        await remove_team_from_report_jobs(
            self._session,
            organization_id=user.organization_id,
            team_id=team.id,
        )
        await self._teams.delete(team)
        await self._session.commit()

    async def _require_team(self, organization_id: UUID, team_id: UUID) -> Team:
        team = await self._teams.get_by_id(team_id, organization_id)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )
        return team

    @staticmethod
    def _to_response(
        team: Team,
        *,
        member_count: int = 0,
        metrics: TeamMetrics | None = None,
    ) -> TeamResponse:
        tool_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            description=team.description,
            active=team.active,
            member_count=member_count,
            token_budget=team.token_budget,
            cost_budget=team.cost_budget,
            tool_ids=[str(tool_id) for tool_id in tool_ids],
            tokens_used=metrics.tokens_used if metrics else 0,
            pricing_total=metrics.pricing_total if metrics else Decimal("0"),
            total_cost=metrics.total_cost if metrics else Decimal("0"),
            last_synced_at=metrics.last_synced_at if metrics else None,
            created_at=team.created_at,
        )
