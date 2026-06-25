"""Resolve Copilot billing CSV user_login values to application users."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.collector import UsageEvent
from app.models.copilot import CopilotUserUsage
from app.teams.membership_repository import TeamMembershipRepository
from app.users.repository import UserAdminRepository


def register_login_alias(lookup: dict[str, UUID], login: str, user_id: UUID) -> None:
    key = login.strip().lower()
    if not key:
        return
    lookup[key] = user_id
    if "@" in key:
        local = key.split("@", 1)[0].strip()
        if local:
            lookup[local] = user_id


def build_copilot_user_lookup(users: list[User]) -> dict[str, UUID]:
    lookup: dict[str, UUID] = {}
    for user in users:
        register_login_alias(lookup, user.email, user.id)
        if user.display_name and user.display_name.strip():
            register_login_alias(lookup, user.display_name.strip(), user.id)
    return lookup


def match_copilot_user_login(
    login: str | None,
    users_by_login: dict[str, UUID],
) -> UUID | None:
    if not login or not str(login).strip():
        return None
    key = str(login).strip().lower()
    matched = users_by_login.get(key)
    if matched is not None:
        return matched
    if "@" in key:
        return users_by_login.get(key.split("@", 1)[0].strip())
    return None


async def build_team_copilot_user_lookup(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team_id: UUID,
) -> dict[str, UUID]:
    memberships = await TeamMembershipRepository(session).list_active_for_team(team_id)
    member_ids = {row.user_id for row in memberships}
    if not member_ids:
        return {}

    org_users = await UserAdminRepository(session).list_by_organization(organization_id)
    team_users = [user for user in org_users if user.id in member_ids]
    lookup = build_copilot_user_lookup(team_users)
    member_by_email = {user.email.lower(): user.id for user in team_users}

    usage_rows = await session.execute(
        select(UsageEvent.user_email, UsageEvent.user_id).where(
            UsageEvent.team_id == team_id,
            UsageEvent.user_id.in_(member_ids),
            UsageEvent.user_email.isnot(None),
        )
    )
    for email, user_id in usage_rows.all():
        if email and user_id:
            register_login_alias(lookup, str(email), user_id)

    copilot_usage = await session.execute(
        select(CopilotUserUsage.user_login, CopilotUserUsage.user_email).where(
            CopilotUserUsage.team_id == team_id,
        )
    )
    for login, email in copilot_usage.all():
        login_text = str(login or "").strip()
        email_text = str(email or "").strip().lower()
        user_id = member_by_email.get(email_text)
        if user_id is None and email_text:
            user_id = lookup.get(email_text)
        if user_id is None and login_text:
            user_id = match_copilot_user_login(login_text, lookup)
        if user_id is not None and login_text:
            register_login_alias(lookup, login_text, user_id)

    return lookup
