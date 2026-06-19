"""Deliver in-app notifications when threshold alerts fire."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Threshold, ThresholdEvent
from app.notifications.repository import NotificationRepository
from app.teams.membership_repository import TeamMembershipRepository
from app.users.repository import UserAdminRepository

ADMIN_ROLES = frozenset({"super_admin", "team_admin"})


async def resolve_recipient_user_ids(
    session: AsyncSession,
    threshold: Threshold,
) -> list[UUID]:
    """Return user IDs who should receive an in-app alert for this threshold."""
    users_repo = UserAdminRepository(session)
    org_users = await users_repo.list_by_organization(threshold.organization_id)
    admins = [user for user in org_users if user.role in ADMIN_ROLES]

    if threshold.scope == "user" and threshold.user_id is not None:
        return [threshold.user_id]

    if threshold.scope == "team" and threshold.team_id is not None:
        memberships = TeamMembershipRepository(session)
        member_user_ids = {
            row.user_id
            for row in await memberships.list_active_for_team(threshold.team_id)
        }
        scoped = [user for user in admins if user.id in member_user_ids]
        super_admins = [user for user in admins if user.role_name == "super_admin"]
        recipient_ids = {user.id for user in super_admins + scoped}
        return list(recipient_ids)

    return [user.id for user in admins]


async def deliver_threshold_breach_notifications(
    session: AsyncSession,
    *,
    threshold: Threshold,
    event: ThresholdEvent,
    current_value: str,
) -> int:
    """Create in-app notification rows for scoped users. Returns count created."""
    if not threshold.notify_in_app:
        return 0

    repo = NotificationRepository(session)
    recipient_ids = await resolve_recipient_user_ids(session, threshold)
    if not recipient_ids:
        return 0

    deep_link = "/alerts/history"
    payload = {
        "threshold_id": str(threshold.id),
        "threshold_event_id": str(event.id),
        "deep_link": deep_link,
        "team_id": str(threshold.team_id) if threshold.team_id else None,
    }
    title = f"Alert: {threshold.name}"
    body = event.message

    created = 0
    for user_id in recipient_ids:
        await repo.create(
            organization_id=threshold.organization_id,
            user_id=user_id,
            notification_type="threshold_breach",
            severity=threshold.severity,
            title=title,
            body=body,
            payload=payload,
            threshold_event_id=event.id,
        )
        created += 1
    return created
