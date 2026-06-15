"""Dashboard widgets derived from admin tools/teams metrics."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthenticatedUser
from app.models.admin import Team, Tool


def _cfg_number(config: dict, key: str, default: float = 0) -> float:
    value = config.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def _usage_for_period(
    config: dict, from_dt: datetime, to_dt: datetime
) -> tuple[int, float]:
    """Sum daily usage within the requested period, else fall back to totals."""
    daily = config.get("daily_usage") or []
    if daily:
        tokens = 0
        cost = 0.0
        from_date = from_dt.date()
        to_date = to_dt.date()
        for point in daily:
            if not isinstance(point, dict):
                continue
            date_key = str(point.get("date", ""))[:10]
            if not date_key:
                continue
            try:
                day = datetime.fromisoformat(date_key).date()
            except ValueError:
                continue
            if from_date <= day <= to_date:
                tokens += int(_cfg_number(point, "tokens"))
                cost += _cfg_number(point, "cost")
        if tokens > 0 or cost > 0:
            return tokens, round(cost, 2)
    return int(_cfg_number(config, "token_count")), _cfg_number(config, "cost_total")


class DashboardService:
    """Compute dashboard widgets from persisted tool/team metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _tools(self, org_id: uuid.UUID) -> list[Tool]:
        stmt = select(Tool).where(Tool.organization_id == org_id)
        return list((await self._session.scalars(stmt)).all())

    async def _teams(self, org_id: uuid.UUID) -> list[Team]:
        stmt = select(Team).where(Team.organization_id == org_id)
        return list((await self._session.scalars(stmt)).all())

    async def get_summary(
        self,
        user: AuthenticatedUser,
        *,
        from_dt: datetime,
        to_dt: datetime,
        team_id: uuid.UUID | None = None,
        tool_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        tools = await self._tools(user.organization_id)
        teams = await self._teams(user.organization_id)

        if tool_id is not None:
            tools = [tool for tool in tools if tool.id == tool_id]
        if team_id is not None:
            teams = [team for team in teams if team.id == team_id]

        total_tokens = sum(
            int(_cfg_number(tool.pricing_config or {}, "token_count")) for tool in tools
        )
        total_cost = sum(
            _cfg_number(tool.pricing_config or {}, "cost_total") for tool in tools
        )
        active_tools = sum(1 for tool in tools if tool.active)
        active_teams = sum(1 for team in teams if team.active)

        prev_tokens = sum(
            int(_cfg_number(tool.pricing_config or {}, "prev_token_count")) for tool in tools
        )
        prev_cost = sum(
            _cfg_number(tool.pricing_config or {}, "prev_cost_total") for tool in tools
        )

        def pct_delta(current: float, previous: float) -> float:
            if previous <= 0:
                return 0.0 if current <= 0 else 100.0
            return round(((current - previous) / previous) * 100, 1)

        return {
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 2),
            "active_tools": active_tools,
            "active_teams": active_teams,
            "tokens_delta": pct_delta(float(total_tokens), float(prev_tokens)),
            "cost_delta": pct_delta(total_cost, prev_cost),
            "tools_delta": 0.0,
            "teams_delta": pct_delta(float(active_teams), float(max(active_teams - 1, 0))),
            "period_from": from_dt.isoformat(),
            "period_to": to_dt.isoformat(),
            "last_updated_at": datetime.now(UTC).isoformat(),
        }

    async def get_tokens_widget(
        self, user: AuthenticatedUser, **filters: Any
    ) -> dict[str, Any]:
        summary = await self.get_summary(user, **filters)
        total = int(summary["total_tokens"])
        return {
            "input_tokens": int(total * 0.6),
            "output_tokens": int(total * 0.4),
            "total_tokens": total,
            "last_updated_at": summary["last_updated_at"],
        }

    async def get_cost_widget(
        self, user: AuthenticatedUser, **filters: Any
    ) -> dict[str, Any]:
        summary = await self.get_summary(user, **filters)
        spend = Decimal(str(summary["total_cost"]))
        return {
            "actual_spend": spend,
            "package_allowance": None,
            "overage_cost": Decimal("0"),
            "last_updated_at": summary["last_updated_at"],
        }

    async def get_usage_by_tool(
        self, user: AuthenticatedUser, **filters: Any
    ) -> dict[str, Any]:
        tools = await self._tools(user.organization_id)
        tool_id = filters.get("tool_id")
        if tool_id is not None:
            tools = [tool for tool in tools if tool.id == tool_id]

        rows = []
        total_tokens = 0
        for tool in tools:
            tokens = int(_cfg_number(tool.pricing_config or {}, "token_count"))
            total_tokens += tokens
            rows.append(
                {
                    "tool_id": str(tool.id),
                    "tool_name": tool.name,
                    "total_tokens": tokens,
                    "estimated_cost": _cfg_number(tool.pricing_config or {}, "cost_total"),
                }
            )

        for row in rows:
            row["share_pct"] = (
                round((row["total_tokens"] / total_tokens) * 100, 2)
                if total_tokens > 0
                else 0.0
            )

        rows.sort(key=lambda item: item["total_tokens"], reverse=True)
        return {
            "data": rows,
            "last_updated_at": datetime.now(UTC).isoformat(),
        }

    async def get_usage_by_team(
        self, user: AuthenticatedUser, **filters: Any
    ) -> dict[str, Any]:
        """Usage broken down by API team (admin.tools), not member groups."""
        tools = await self._tools(user.organization_id)
        tool_id = filters.get("tool_id")
        team_id = filters.get("team_id")
        selected_id = tool_id or team_id
        if selected_id is not None:
            tools = [tool for tool in tools if tool.id == selected_id]

        from_dt = filters.get("from_dt")
        to_dt = filters.get("to_dt")

        data = []
        for tool in tools:
            if not tool.active:
                continue
            config = tool.pricing_config or {}
            if from_dt is not None and to_dt is not None:
                tokens, cost = _usage_for_period(config, from_dt, to_dt)
            else:
                tokens = int(_cfg_number(config, "token_count"))
                cost = _cfg_number(config, "cost_total")
            data.append(
                {
                    "team_id": str(tool.id),
                    "team_name": tool.name,
                    "total_tokens": tokens,
                    "estimated_cost": round(cost, 2),
                }
            )
        data.sort(key=lambda item: item["total_tokens"], reverse=True)
        return {
            "data": data,
            "last_updated_at": datetime.now(UTC).isoformat(),
        }

    async def get_top_consumers(
        self,
        user: AuthenticatedUser,
        *,
        from_dt: datetime,
        to_dt: datetime,
        limit: int = 10,
        team_id: uuid.UUID | None = None,
        tool_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        teams = await self.get_usage_by_team(
            user,
            from_dt=from_dt,
            to_dt=to_dt,
            team_id=team_id,
            tool_id=tool_id,
        )
        rows = [
            {
                "entity_id": row["team_id"],
                "entity_name": row["team_name"],
                "total_tokens": row["total_tokens"],
                "estimated_cost": row["estimated_cost"],
                "entity_type": "team",
            }
            for row in teams["data"]
        ]
        rows.sort(key=lambda item: item["total_tokens"], reverse=True)
        return {"data": rows[:limit]}

    async def get_trends(
        self,
        user: AuthenticatedUser,
        *,
        from_dt: datetime,
        to_dt: datetime,
        granularity: str = "daily",
        team_id: uuid.UUID | None = None,
        tool_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        tools = await self._tools(user.organization_id)
        if tool_id is not None:
            tools = [tool for tool in tools if tool.id == tool_id]

        daily: dict[str, dict[str, float]] = {}
        for tool in tools:
            config = tool.pricing_config or {}
            for point in config.get("daily_usage", []):
                if not isinstance(point, dict):
                    continue
                date_key = str(point.get("date", ""))[:10]
                if not date_key:
                    continue
                bucket = daily.setdefault(date_key, {"tokens": 0.0, "cost": 0.0})
                bucket["tokens"] += _cfg_number(point, "tokens")
                bucket["cost"] += _cfg_number(point, "cost")

        if not daily:
            summary = await self.get_summary(
                user,
                from_dt=from_dt,
                to_dt=to_dt,
                team_id=team_id,
                tool_id=tool_id,
            )
            days = max(1, (to_dt.date() - from_dt.date()).days + 1)
            per_day_tokens = int(summary["total_tokens"]) // days
            per_day_cost = float(summary["total_cost"]) / days
            cursor = from_dt.date()
            while cursor <= to_dt.date():
                daily[cursor.isoformat()] = {
                    "tokens": float(per_day_tokens),
                    "cost": per_day_cost,
                }
                cursor += timedelta(days=1)

        data = [
            {
                "period_start": f"{date_key}T00:00:00Z",
                "total_tokens": int(values["tokens"]),
                "estimated_cost": round(values["cost"], 2),
            }
            for date_key, values in sorted(daily.items())
        ]
        return {"data": data, "granularity": granularity}

    async def get_alerts(self, user: AuthenticatedUser) -> dict[str, Any]:
        """Return active alert summaries (empty until notifications backend)."""
        return {"data": [], "last_updated_at": datetime.now(UTC).isoformat()}

    @staticmethod
    def apply_usage_snapshot(
        config: dict,
        *,
        token_count: int,
        cost_total: float,
        daily_usage: list | None,
    ) -> dict:
        """Replace tool metrics with live usage pulled from a vendor API."""
        updated = dict(config)
        updated["prev_token_count"] = int(_cfg_number(updated, "token_count"))
        updated["prev_cost_total"] = _cfg_number(updated, "cost_total")
        updated["token_count"] = int(token_count)
        updated["cost_total"] = round(float(cost_total), 2)
        if daily_usage is not None:
            updated["daily_usage"] = daily_usage[-90:]
        updated["last_sync_at"] = datetime.now(UTC).isoformat()
        return updated

    @staticmethod
    def merge_usage_snapshot(
        config: dict,
        *,
        token_count: int,
        cost_total: float,
        daily_usage: list | None,
    ) -> dict:
        """Merge imported usage into existing daily metrics by date."""
        updated = dict(config)
        existing_daily = {
            str(row.get("date", ""))[:10]: row
            for row in (updated.get("daily_usage") or [])
            if isinstance(row, dict)
        }

        for row in daily_usage or []:
            if not isinstance(row, dict):
                continue
            day = str(row.get("date", ""))[:10]
            if not day:
                continue
            if day in existing_daily:
                existing = existing_daily[day]
                existing["tokens"] = int(existing.get("tokens", 0)) + int(row.get("tokens", 0))
                existing["cost"] = round(
                    float(existing.get("cost", 0)) + float(row.get("cost", 0)),
                    2,
                )
            else:
                existing_daily[day] = {
                    "date": day,
                    "tokens": int(row.get("tokens", 0)),
                    "cost": round(float(row.get("cost", 0)), 2),
                }

        merged_daily = [
            {
                "date": day,
                "tokens": int(values.get("tokens", 0)),
                "cost": round(float(values.get("cost", 0)), 2),
            }
            for day, values in sorted(existing_daily.items())
        ]
        merged_tokens = sum(item["tokens"] for item in merged_daily)
        merged_cost = round(sum(item["cost"] for item in merged_daily), 2)

        return DashboardService.apply_usage_snapshot(
            updated,
            token_count=merged_tokens,
            cost_total=merged_cost,
            daily_usage=merged_daily,
        )

    @staticmethod
    def apply_sync_metrics(config: dict) -> dict:
        """Bump usage metrics when a tool sync occurs."""
        updated = dict(config)
        tokens = int(_cfg_number(updated, "token_count"))
        cost = _cfg_number(updated, "cost_total")
        updated["prev_token_count"] = tokens
        updated["prev_cost_total"] = cost

        bump_tokens = max(1000, int(tokens * 0.02)) if tokens else 5000
        bump_cost = max(0.5, cost * 0.02) if cost else 2.5
        updated["token_count"] = tokens + bump_tokens
        updated["cost_total"] = round(cost + bump_cost, 2)
        updated["last_sync_at"] = datetime.now(UTC).isoformat()

        today = datetime.now(UTC).date().isoformat()
        daily_usage = list(updated.get("daily_usage", []))
        if daily_usage and daily_usage[-1].get("date", "")[:10] == today:
            daily_usage[-1]["tokens"] = int(daily_usage[-1].get("tokens", 0)) + bump_tokens
            daily_usage[-1]["cost"] = round(
                float(daily_usage[-1].get("cost", 0)) + bump_cost, 2
            )
        else:
            daily_usage.append(
                {"date": today, "tokens": bump_tokens, "cost": round(bump_cost, 2)}
            )
        updated["daily_usage"] = daily_usage[-90:]
        return updated
