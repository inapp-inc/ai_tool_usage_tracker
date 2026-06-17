"""Team–tool assignment business logic."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.admin import Team, TeamTool, Tool
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository
from app.teams.schemas import (
    PaginationMeta,
    TeamSyncResponse,
    TeamToolAssignRequest,
    TeamToolAssignmentListResponse,
    TeamToolAssignmentResponse,
    TeamToolSyncResult,
    TeamToolUpdateRequest,
)
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.pricing import merge_pricing_config, normalize_pricing_config, validate_pricing_model
from app.tools.repository import ToolRepository
from app.tools.service import ToolService

WRITE_ROLES = frozenset({"super_admin", "team_admin"})


class TeamToolService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)
        self._team_tools = TeamToolRepository(session)
        self._tools = ToolRepository(session)
        self._memberships = TeamMembershipRepository(session)

    async def list_assignments(
        self,
        user: User,
        team_id: UUID,
    ) -> TeamToolAssignmentListResponse:
        team = await self._require_team_access(user, team_id)
        rows = await self._team_tools.list_by_team(team.id)
        tool_names = await self._tool_name_map(user.organization_id, [row.tool_id for row in rows])
        data = [self._to_response(row, tool_names.get(row.tool_id, "")) for row in rows]
        return TeamToolAssignmentListResponse(
            data=data,
            meta=PaginationMeta(has_more=False),
        )

    async def create_assignment(
        self,
        user: User,
        team_id: UUID,
        body: TeamToolAssignRequest,
    ) -> TeamToolAssignmentResponse:
        team = await self._require_team_access(user, team_id, write=True)
        tool = await self._require_tool(user.organization_id, body.tool_id)

        existing = await self._team_tools.get_by_team_and_tool(team.id, tool.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tool is already assigned to this team.",
            )

        assignment = TeamTool(team_id=team.id, tool_id=tool.id)
        self._apply_pricing_fields(assignment, body)
        await self._team_tools.create(assignment)
        await self._ensure_tool_on_team(team, tool.id)
        await self._session.commit()
        await self._session.refresh(assignment)
        return self._to_response(assignment, tool.name)

    async def update_assignment(
        self,
        user: User,
        team_id: UUID,
        tool_id: UUID,
        body: TeamToolUpdateRequest,
    ) -> TeamToolAssignmentResponse:
        team = await self._require_team_access(user, team_id, write=True)
        tool = await self._require_tool(user.organization_id, tool_id)
        assignment = await self._require_assignment(team.id, tool.id)
        self._apply_pricing_fields(assignment, body)
        await self._session.commit()
        await self._session.refresh(assignment)
        return self._to_response(assignment, tool.name)

    async def delete_assignment(
        self,
        user: User,
        team_id: UUID,
        tool_id: UUID,
    ) -> None:
        team = await self._require_team_access(user, team_id, write=True)
        assignment = await self._require_assignment(team.id, tool_id)
        await self._team_tools.delete(assignment)
        await self._remove_tool_from_team(team, tool_id)
        await self._session.commit()

    async def sync_team_tools(
        self,
        user: User,
        team_id: UUID,
    ) -> TeamSyncResponse:
        """Pull usage/members from providers for all credentialed tools on this team."""
        team = await self._require_team_access(user, team_id, write=True)
        tool_service = ToolService(self._session)
        tool_ids = await self._collect_team_tool_ids(team)
        results: list[TeamToolSyncResult] = []

        for tool_id in tool_ids:
            tool = await self._tools.get_by_id(tool_id, user.organization_id)
            if tool is None:
                continue

            if not ToolService._decrypt_api_key(tool):
                results.append(
                    TeamToolSyncResult(
                        tool_id=tool.id,
                        tool_name=tool.name,
                        status="skipped",
                        message="No credentials connected.",
                    )
                )
                continue

            try:
                await tool_service.sync_tool(user.organization_id, tool.id)
                results.append(
                    TeamToolSyncResult(
                        tool_id=tool.id,
                        tool_name=tool.name,
                        status="synced",
                        message="Usage data collected.",
                    )
                )
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                results.append(
                    TeamToolSyncResult(
                        tool_id=tool.id,
                        tool_name=tool.name,
                        status="failed",
                        message=detail,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                results.append(
                    TeamToolSyncResult(
                        tool_id=tool.id,
                        tool_name=tool.name,
                        status="failed",
                        message=str(exc)[:200],
                    )
                )

        synced_count = sum(1 for row in results if row.status == "synced")
        skipped_count = sum(1 for row in results if row.status == "skipped")
        failed_count = sum(1 for row in results if row.status == "failed")

        return TeamSyncResponse(
            team_id=team.id,
            synced_count=synced_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results,
        )

    async def _collect_team_tool_ids(self, team: Team) -> list[UUID]:
        ids: set[UUID] = set()
        raw_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
        for raw in raw_ids:
            try:
                ids.add(UUID(str(raw)))
            except ValueError:
                continue

        assignments = await self._team_tools.list_by_team(team.id)
        for assignment in assignments:
            ids.add(assignment.tool_id)

        return sorted(ids, key=str)

    async def _require_team_access(
        self,
        user: User,
        team_id: UUID,
        *,
        write: bool = False,
    ) -> Team:
        team = await self._teams.get_by_id(team_id, user.organization_id)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )

        if user.role == "super_admin":
            return team

        if user.role == "team_admin":
            allowed = await self._memberships.active_team_ids_for_user(user.id)
            if team_id not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this team.",
                )
            return team

        if write:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )

    async def _require_tool(self, organization_id: UUID, tool_id: UUID) -> Tool:
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found.",
            )
        return tool

    async def _require_assignment(self, team_id: UUID, tool_id: UUID) -> TeamTool:
        assignment = await self._team_tools.get_by_team_and_tool(team_id, tool_id)
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team tool assignment not found.",
            )
        return assignment

    async def _tool_name_map(
        self,
        organization_id: UUID,
        tool_ids: list[UUID],
    ) -> dict[UUID, str]:
        if not tool_ids:
            return {}
        tools = await self._tools.list_by_organization(organization_id, active=None)
        return {tool.id: tool.name for tool in tools if tool.id in set(tool_ids)}

    async def _ensure_tool_on_team(self, team: Team, tool_id: UUID) -> None:
        tool_id_str = str(tool_id)
        tool_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
        if tool_id_str in tool_ids:
            return
        team.tool_ids = [*tool_ids, tool_id_str]
        flag_modified(team, "tool_ids")

    async def _remove_tool_from_team(self, team: Team, tool_id: UUID) -> None:
        tool_id_str = str(tool_id)
        tool_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
        team.tool_ids = [value for value in tool_ids if value != tool_id_str]
        flag_modified(team, "tool_ids")

    def _apply_pricing_fields(
        self,
        assignment: TeamTool,
        body: TeamToolAssignRequest | TeamToolUpdateRequest,
    ) -> None:
        updates = body.model_fields_set

        if "pricing_model" in updates:
            if body.pricing_model is not None:
                validate_pricing_model(body.pricing_model)
            assignment.pricing_model = body.pricing_model

        if "token_price" in updates:
            assignment.token_price = body.token_price
        if "output_token_price" in updates:
            assignment.output_token_price = body.output_token_price
        if "cost_per_seat" in updates:
            assignment.cost_per_seat = body.cost_per_seat
        if "seat_count" in updates:
            assignment.seat_count = body.seat_count
        if "package_allowance" in updates:
            assignment.package_allowance = body.package_allowance
        if "overage_price" in updates:
            assignment.overage_price = body.overage_price
        if "plan_name" in updates:
            assignment.plan_name = body.plan_name.strip() if body.plan_name else None

        if "pricing_config" in updates and body.pricing_config is not None:
            existing = (
                assignment.pricing_config
                if isinstance(assignment.pricing_config, dict)
                else {}
            )
            assignment.pricing_config = merge_pricing_config(existing, body.pricing_config)

        pricing_model = assignment.pricing_model or "flat_token"
        assignment.pricing_config = normalize_pricing_config(
            pricing_model,
            assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {},
            package_allowance=assignment.package_allowance,
            overage_price=assignment.overage_price,
        )

    @staticmethod
    def _to_response(assignment: TeamTool, tool_name: str) -> TeamToolAssignmentResponse:
        config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
        return TeamToolAssignmentResponse(
            id=assignment.id,
            team_id=assignment.team_id,
            tool_id=assignment.tool_id,
            tool_name=tool_name,
            pricing_model=assignment.pricing_model,
            token_price=assignment.token_price,
            output_token_price=assignment.output_token_price,
            cost_per_seat=assignment.cost_per_seat,
            seat_count=assignment.seat_count,
            package_allowance=assignment.package_allowance,
            overage_price=assignment.overage_price,
            plan_name=assignment.plan_name,
            pricing_config=config,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )
