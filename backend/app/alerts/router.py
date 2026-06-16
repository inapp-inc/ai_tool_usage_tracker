"""Alert rules API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.service import AlertService
from app.auth.service import AuthenticatedUser
from app.core.rbac import get_managed_team_ids, require_team_admin_or_above
from app.db.session import get_session

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertRuleBody(BaseModel):
    name: str
    severity: str
    threshold_type: str
    threshold_value: float
    scope: str
    team_id: str | None = None
    team_name: str | None = None
    channel: str
    webhook_url: str | None = None
    email_recipients: list[str] = Field(default_factory=list)
    status: str = "active"


class AlertRuleUpdateBody(BaseModel):
    name: str | None = None
    severity: str | None = None
    threshold_type: str | None = None
    threshold_value: float | None = None
    scope: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    channel: str | None = None
    webhook_url: str | None = None
    email_recipients: list[str] | None = None
    status: str | None = None


@router.get("/rules", operation_id="listAlertRules")
async def list_alert_rules(
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    rules = await service.list_rules(current_user)
    if current_user.role == "team_admin":
        managed_ids_str = {str(tid) for tid in managed_team_ids}
        rules = [r for r in rules if str(r.get("team_id", "")) in managed_ids_str]
    return {"data": rules}


@router.post("/rules", status_code=status.HTTP_201_CREATED, operation_id="createAlertRule")
async def create_alert_rule(
    body: AlertRuleBody,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if current_user.role == "team_admin":
        if not managed_team_ids:
            raise HTTPException(status_code=403, detail="You are not a member of any team.")
        if body.team_id and uuid.UUID(body.team_id) not in managed_team_ids:
            raise HTTPException(status_code=403, detail="You can only create alerts for your own team.")
        if not body.team_id:
            body = body.model_copy(update={
                "team_id": str(managed_team_ids[0]),
                "scope": "team",
            })

    service = AlertService(session)
    return {"data": await service.create_rule(current_user, body.model_dump())}


@router.patch("/rules/{rule_id}", operation_id="updateAlertRule")
async def update_alert_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdateBody,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    if current_user.role == "team_admin":
        existing_rule = await service.get_rule(current_user, str(rule_id))
        if existing_rule is None:
            raise HTTPException(status_code=404, detail="Alert rule not found.")
        managed_ids_str = {str(tid) for tid in managed_team_ids}
        if str(existing_rule.get("team_id", "")) not in managed_ids_str:
            raise HTTPException(status_code=403, detail="You do not have access to this alert rule.")

    updated = await service.update_rule(
        current_user,
        str(rule_id),
        body.model_dump(exclude_unset=True),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    return {"data": updated}


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = AlertService(session)
    if current_user.role == "team_admin":
        existing_rule = await service.get_rule(current_user, str(rule_id))
        if existing_rule is None:
            raise HTTPException(status_code=404, detail="Alert rule not found.")
        managed_ids_str = {str(tid) for tid in managed_team_ids}
        if str(existing_rule.get("team_id", "")) not in managed_ids_str:
            raise HTTPException(status_code=403, detail="You do not have access to this alert rule.")

    if not await service.delete_rule(current_user, str(rule_id)):
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/events", operation_id="listAlertEvents")
async def list_alert_events(
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    events = await service.list_events(current_user)
    if current_user.role == "team_admin":
        managed_ids_str = {str(tid) for tid in managed_team_ids}
        events = [e for e in events if str(e.get("team_id", "")) in managed_ids_str]
    return {"data": events}


@router.post("/events/{event_id}/acknowledge", operation_id="acknowledgeAlertEvent")
async def acknowledge_alert_event(
    event_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_team_admin_or_above),
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    if current_user.role == "team_admin":
        events = await service.list_events(current_user)
        event = next((e for e in events if e.get("id") == str(event_id)), None)
        if event is None:
            raise HTTPException(status_code=404, detail="Alert event not found.")
        managed_ids_str = {str(tid) for tid in managed_team_ids}
        if str(event.get("team_id", "")) not in managed_ids_str:
            raise HTTPException(status_code=403, detail="You do not have access to this alert event.")

    updated = await service.acknowledge_event(current_user, str(event_id))
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert event not found.")
    return {"data": updated}
