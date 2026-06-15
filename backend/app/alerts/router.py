"""Alert rules API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.service import AlertService
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
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
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    return {"data": await service.list_rules(current_user)}


@router.post("/rules", status_code=status.HTTP_201_CREATED, operation_id="createAlertRule")
async def create_alert_rule(
    body: AlertRuleBody,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    return {"data": await service.create_rule(current_user, body.model_dump())}


@router.patch("/rules/{rule_id}", operation_id="updateAlertRule")
async def update_alert_rule(
    rule_id: uuid.UUID,
    body: AlertRuleUpdateBody,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
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
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = AlertService(session)
    if not await service.delete_rule(current_user, str(rule_id)):
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/events", operation_id="listAlertEvents")
async def list_alert_events(
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    return {"data": await service.list_events(current_user)}


@router.post("/events/{event_id}/acknowledge", operation_id="acknowledgeAlertEvent")
async def acknowledge_alert_event(
    event_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = AlertService(session)
    updated = await service.acknowledge_event(current_user, str(event_id))
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert event not found.")
    return {"data": updated}
