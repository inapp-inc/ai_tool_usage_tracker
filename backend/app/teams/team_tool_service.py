"""Team–tool assignment business logic."""

import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.permissions import ORG_WIDE_ROLE_NAMES
from app.models.admin import Team, TeamTool, Tool, ToolPackage
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository
from app.teams.team_tool_repository import TeamToolRepository
from app.teams.schemas import (
    PaginationMeta,
    TeamSyncResponse,
    TeamToolAssignRequest,
    TeamToolAssignmentListResponse,
    TeamToolAssignmentResponse,
    TeamToolSyncResult,
    TeamToolUpdateRequest,
)
from app.teams.team_tool_alert_sync import sync_team_tool_cost_alert
from app.tools.catalogue import catalogue_tool_id_from_connected, connected_to_catalogue_map, team_id_from_connected
from app.tools.pricing import merge_pricing_config, normalize_pricing_config, validate_pricing_model
from app.tools.repository import ToolRepository
from app.tools.service import ToolService

logger = logging.getLogger(__name__)


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
        tool = await self._require_tool(team.organization_id, body.tool_id)

        existing = await self._team_tools.get_by_team_and_tool(team.id, tool.id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tool is already assigned to this team.",
            )

        assignment = TeamTool(team_id=team.id, tool_id=tool.id)
        self._apply_pricing_fields(assignment, body)
        await self._apply_package_binding(assignment, body, tool)
        self._apply_subscription_fields(assignment, body)
        self._sync_figma_pricing_config(assignment, body, tool)
        self._validate_copilot_assignment(tool, assignment)
        self._validate_figma_assignment(tool, assignment)
        await self._team_tools.create(assignment)
        await self._ensure_tool_on_team(team, tool.id)
        await sync_team_tool_cost_alert(
            self._session,
            organization_id=team.organization_id,
            team=team,
            tool=tool,
            assignment=assignment,
        )
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
        tool = await self._require_tool(team.organization_id, tool_id)
        assignment = await self._require_assignment(team.id, tool.id)
        self._apply_pricing_fields(assignment, body)
        await self._apply_package_binding(assignment, body, tool)
        self._apply_subscription_fields(assignment, body)
        self._sync_figma_pricing_config(assignment, body, tool)
        self._validate_copilot_assignment(tool, assignment)
        self._validate_figma_assignment(tool, assignment)
        await sync_team_tool_cost_alert(
            self._session,
            organization_id=team.organization_id,
            team=team,
            tool=tool,
            assignment=assignment,
        )
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
        """Pull usage/members from all connected credentials assigned to this team."""
        await self._require_team_access(user, team_id, write=True)
        return await self.sync_team_tools_for_organization(user.organization_id, team_id)

    async def sync_team_tools_for_organization(
        self,
        organization_id: UUID,
        team_id: UUID,
    ) -> TeamSyncResponse:
        """Sync all connected credentials for a team (API and background jobs)."""
        team = await self._teams.get_by_id(team_id, organization_id)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )

        tool_service = ToolService(self._session)
        org_tools = await self._tools.list_by_organization(organization_id, active=None)
        id_to_catalogue = connected_to_catalogue_map(org_tools)
        raw_tool_ids = set(await self._collect_team_tool_ids(team))
        catalogue_tool_ids = {id_to_catalogue.get(tool_id, tool_id) for tool_id in raw_tool_ids}
        connected_tools = await self._tools.list_connected_for_team(
            organization_id,
            team_id=team.id,
            catalogue_tool_ids=catalogue_tool_ids,
        )
        logger.info(
            "Team sync started | org=%s team_id=%s assigned_tools=%s connected_credentials=%s",
            organization_id,
            team_id,
            len(catalogue_tool_ids),
            len(connected_tools),
        )
        results: list[TeamToolSyncResult] = []

        for connected in connected_tools:
            catalogue_id = catalogue_tool_id_from_connected(connected)
            if catalogue_id is not None:
                await self._ensure_tool_on_team(team, catalogue_id)
            if team_id_from_connected(connected) != team.id:
                config = (
                    dict(connected.pricing_config)
                    if isinstance(connected.pricing_config, dict)
                    else {}
                )
                config["team_id"] = str(team.id)
                connected.pricing_config = config
                flag_modified(connected, "pricing_config")
            catalogue_tool = (
                await self._tools.get_by_id(catalogue_id, organization_id)
                if catalogue_id is not None
                else None
            )
            display_name = self._sync_display_name(catalogue_tool, connected)

            if not ToolService._decrypt_api_key(connected):
                results.append(
                    TeamToolSyncResult(
                        tool_id=catalogue_id or connected.id,
                        tool_name=display_name,
                        status="skipped",
                        message="No credentials connected.",
                    )
                )
                continue

            try:
                await tool_service.sync_tool(organization_id, connected.id)
                results.append(
                    TeamToolSyncResult(
                        tool_id=catalogue_id or connected.id,
                        tool_name=display_name,
                        status="synced",
                        message="Usage data collected.",
                    )
                )
                logger.info(
                    "Team sync tool ok | team_id=%s connected_id=%s vendor=%s name=%s",
                    team_id,
                    connected.id,
                    connected.vendor,
                    display_name,
                )
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                logger.warning(
                    "Team sync tool failed | team_id=%s connected_id=%s vendor=%s detail=%s",
                    team_id,
                    connected.id,
                    connected.vendor,
                    detail,
                )
                results.append(
                    TeamToolSyncResult(
                        tool_id=catalogue_id or connected.id,
                        tool_name=display_name,
                        status="failed",
                        message=detail,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Team sync tool error | team_id=%s connected_id=%s vendor=%s",
                    team_id,
                    connected.id,
                    connected.vendor,
                )
                results.append(
                    TeamToolSyncResult(
                        tool_id=catalogue_id or connected.id,
                        tool_name=display_name,
                        status="failed",
                        message=str(exc)[:200],
                    )
                )

        await self._session.commit()

        connected_catalogue_ids = {
            catalogue_tool_id_from_connected(row)
            for row in connected_tools
            if catalogue_tool_id_from_connected(row) is not None
        }
        for tool_id in sorted(catalogue_tool_ids, key=str):
            if tool_id in connected_catalogue_ids:
                continue
            catalogue_tool = await self._tools.get_by_id(tool_id, organization_id)
            if catalogue_tool is None or not catalogue_tool.catalogue_only:
                continue
            results.append(
                TeamToolSyncResult(
                    tool_id=catalogue_tool.id,
                    tool_name=catalogue_tool.name,
                    status="skipped",
                    message="No credentials connected.",
                )
            )

        synced_count = sum(1 for row in results if row.status == "synced")
        skipped_count = sum(1 for row in results if row.status == "skipped")
        failed_count = sum(1 for row in results if row.status == "failed")

        logger.info(
            "Team sync finished | org=%s team_id=%s synced=%s skipped=%s failed=%s",
            organization_id,
            team_id,
            synced_count,
            skipped_count,
            failed_count,
        )

        return TeamSyncResponse(
            team_id=team.id,
            synced_count=synced_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results,
        )

    @staticmethod
    def _sync_display_name(catalogue_tool: Tool | None, connected: Tool) -> str:
        base_name = catalogue_tool.name if catalogue_tool is not None else connected.name
        label = (connected.credential_label or connected.name or "").strip()
        if label and label.lower() != base_name.lower():
            return f"{base_name} ({label})"
        return base_name

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
        team = await self._teams.get_by_id_unscoped(team_id)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )

        if user.role_name == "super_admin":
            return team

        if user.role_name in ORG_WIDE_ROLE_NAMES:
            if team.organization_id != user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this team.",
                )
            return team

        scoped = await self._teams.get_by_id(team_id, user.organization_id)
        if scoped is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )
        team = scoped

        if user.role_name == "team_admin":
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
        if not tool.catalogue_only:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assign tools from the catalogue only.",
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
    def _sync_figma_pricing_config(
        assignment: TeamTool,
        body: TeamToolAssignRequest | TeamToolUpdateRequest,
        tool: Tool,
    ) -> None:
        if tool.vendor != "figma":
            return
        config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
        if assignment.cost_per_seat is not None:
            config["full_seat_cost_usd"] = str(assignment.cost_per_seat)
            config["cost_per_seat"] = str(assignment.cost_per_seat)
        if assignment.seat_count is not None:
            config["seat_count"] = assignment.seat_count
        if "pricing_config" in body.model_fields_set and body.pricing_config:
            for key in (
                "full_seat_cost_usd",
                "view_seat_cost_usd",
                "credits_per_usd",
                "credit_amount",
                "included_credits_per_seat",
            ):
                if key in body.pricing_config and body.pricing_config[key] is not None:
                    raw = body.pricing_config[key]
                    if key == "included_credits_per_seat":
                        config[key] = int(raw)
                    else:
                        config[key] = str(raw)
        config["provider_slug"] = "figma"
        config["model"] = config.get("model") or "per_seat"
        assignment.pricing_config = config

    def _apply_subscription_fields(
        self,
        assignment: TeamTool,
        body: TeamToolAssignRequest | TeamToolUpdateRequest,
    ) -> None:
        updates = body.model_fields_set
        if "subscription_start" in updates:
            assignment.subscription_start = body.subscription_start
        if "subscription_end" in updates:
            assignment.subscription_end = body.subscription_end
        if "monthly_budget" in updates:
            assignment.monthly_budget = body.monthly_budget
        if "alert_threshold" in updates:
            assignment.alert_threshold = body.alert_threshold
        if "alert_threshold_usd" in updates:
            assignment.alert_threshold_usd = body.alert_threshold_usd

    async def _apply_package_binding(
        self,
        assignment: TeamTool,
        body: TeamToolAssignRequest | TeamToolUpdateRequest,
        tool: Tool,
    ) -> None:
        if "package_id" not in body.model_fields_set:
            return

        package_id = body.package_id
        assignment.package_id = package_id
        if package_id is None:
            return

        package = await self._session.get(ToolPackage, package_id)
        if package is None or not package.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found.",
            )

        catalogue_id = catalogue_tool_id_from_connected(tool) or tool.id
        if package.tool_id != catalogue_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Package does not belong to this tool.",
            )

        assignment.plan_name = package.package_name
        config = (
            dict(assignment.pricing_config)
            if isinstance(assignment.pricing_config, dict)
            else {}
        )
        config["plan_name"] = package.package_name

        if tool.vendor == "copilot" and package.billing_type == "CREDIT_BASED":
            model = str(config.get("model") or "per_seat")
            assignment.pricing_model = "custom"
            if assignment.seat_count is None:
                assignment.seat_count = 1
            config["seat_count"] = assignment.seat_count
            config["model"] = model
            if model == "per_team":
                if config.get("flat_monthly_cost") is None and assignment.cost_per_seat is not None:
                    config["flat_monthly_cost"] = str(assignment.cost_per_seat)
                if config.get("cost_per_team") is None and config.get("flat_monthly_cost") is not None:
                    config["cost_per_team"] = config["flat_monthly_cost"]
                config.pop("cost_per_seat", None)
                assignment.cost_per_seat = None
            else:
                if assignment.cost_per_seat is None and config.get("cost_per_seat") is not None:
                    assignment.cost_per_seat = Decimal(str(config["cost_per_seat"]))
                config["cost_per_seat"] = (
                    str(assignment.cost_per_seat)
                    if assignment.cost_per_seat is not None
                    else None
                )
                config.pop("flat_monthly_cost", None)
                config.pop("cost_per_team", None)
            assignment.pricing_config = config
            return

        if tool.vendor == "copilot" and package.billing_type != "CREDIT_BASED":
            model = str(config.get("model") or "per_seat")
            assignment.pricing_model = "custom"
            if assignment.seat_count is None:
                assignment.seat_count = package.seat_limit or 1
            config["seat_count"] = assignment.seat_count

            if model == "per_team":
                if config.get("flat_monthly_cost") is None and package.monthly_price is not None:
                    config["flat_monthly_cost"] = str(package.monthly_price)
                    config["cost_per_team"] = str(package.monthly_price)
                config["model"] = "per_team"
                assignment.pricing_config = config
                return

            if assignment.cost_per_seat is None and package.monthly_price is not None:
                assignment.cost_per_seat = package.monthly_price
            config["cost_per_seat"] = (
                str(assignment.cost_per_seat)
                if assignment.cost_per_seat is not None
                else None
            )
            config.pop("flat_monthly_cost", None)
            config.pop("cost_per_team", None)
            config["model"] = "per_seat"
            assignment.pricing_config = config
            return

        if package.monthly_price is not None:
            config["flat_monthly_cost"] = str(package.monthly_price)
        assignment.pricing_config = config

        if package.billing_type == "SEAT_BASED":
            assignment.pricing_model = "custom"
            if assignment.seat_count is None and package.seat_limit is not None:
                assignment.seat_count = package.seat_limit
            if assignment.cost_per_seat is None and package.monthly_price is not None:
                assignment.cost_per_seat = package.monthly_price
            config["cost_per_seat"] = (
                str(assignment.cost_per_seat)
                if assignment.cost_per_seat is not None
                else None
            )
            config["seat_count"] = assignment.seat_count
            config.pop("flat_monthly_cost", None)
            config["model"] = "per_seat"
            if tool.vendor == "figma" and assignment.cost_per_seat is not None:
                config["full_seat_cost_usd"] = str(assignment.cost_per_seat)
            assignment.pricing_config = config
            return

        assignment.pricing_model = "package_with_overage"
        allowance: int | None = None
        if package.billing_type == "TOKEN_BASED":
            allowance = package.token_limit
        elif package.billing_type == "REQUEST_BASED":
            allowance = package.request_limit
        elif package.billing_type == "CREDIT_BASED" and package.credit_limit is not None:
            allowance = int(package.credit_limit)
        if allowance is not None:
            assignment.package_allowance = allowance
            config["included_tokens"] = allowance
        assignment.pricing_config = normalize_pricing_config(
            assignment.pricing_model,
            config,
            package_allowance=assignment.package_allowance,
            overage_price=assignment.overage_price,
        )

    @staticmethod
    def _validate_figma_assignment(tool: Tool, assignment: TeamTool) -> None:
        if tool.vendor != "figma":
            return
        if assignment.package_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Figma requires a subscription package.",
            )
        if assignment.seat_count is not None and assignment.seat_count < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Figma seat count must be at least 1.",
            )

    @staticmethod
    def _validate_copilot_assignment(tool: Tool, assignment: TeamTool) -> None:
        if tool.vendor != "copilot":
            return
        if assignment.package_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="GitHub Copilot requires a subscription package.",
            )
        if assignment.seat_count is not None and assignment.seat_count < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Copilot seat count must be at least 1.",
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
            pricing_config=jsonable_encoder(config) if config else {},
            package_id=assignment.package_id,
            subscription_start=assignment.subscription_start,
            subscription_end=assignment.subscription_end,
            monthly_budget=assignment.monthly_budget,
            alert_threshold=assignment.alert_threshold,
            alert_threshold_usd=assignment.alert_threshold_usd,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )
