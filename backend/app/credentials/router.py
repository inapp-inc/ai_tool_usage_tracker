"""Credentials REST API — tool-backed API keys."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder

from app.auth.dependencies import get_current_user
from app.core.org_scope import get_operating_org_scope, OperatingOrgScope, require_operating_organization_id
from app.core.permissions import require_permission
from app.credentials.schemas import (
    CredentialCreateRequest,
    CredentialCreateResponseBody,
    CredentialListResponse,
    CredentialResponse,
    CredentialSecretResponse,
    CredentialUpdateRequest,
    CredentialValidateRequest,
    CredentialValidateResponse,
)
from app.credentials.service import CredentialService
from app.db.session import get_session
from app.models.auth import User
from app.tools.background import run_team_sync_background

router = APIRouter(prefix="/credentials", tags=["Credentials"])

logger = logging.getLogger(__name__)


def get_credential_service(session: AsyncSession = Depends(get_session)) -> CredentialService:
    return CredentialService(session)


async def _reload_scheduler(request: Request) -> None:
    scheduler = getattr(request.app.state, "collector_scheduler", None)
    if scheduler is not None:
        await scheduler.reload()


@router.post("/validate", response_model=CredentialValidateResponse)
async def validate_credential(
    body: CredentialValidateRequest,
    current_user: User = Depends(require_permission("credentials", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialValidateResponse:
    org_id = require_operating_organization_id(scope)
    return await service.validate_credential(org_id, body)


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    current_user: User = Depends(require_permission("credentials", "read")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialListResponse:
    org_id = require_operating_organization_id(scope)
    return await service.list_credentials(org_id)


@router.post("", response_model=CredentialCreateResponseBody, status_code=status.HTTP_201_CREATED)
async def create_credential(
    body: CredentialCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("credentials", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> CredentialCreateResponseBody:
    org_id = require_operating_organization_id(scope)
    created = await service.create_credential(org_id, body)
    logger.info(
        "Credential connected | org=%s team_id=%s catalogue_tool_id=%s credential_id=%s vendor=%s label=%s — scheduling team sync",
        org_id,
        body.team_id,
        body.tool_id,
        created.credential.id,
        created.credential.vendor,
        created.credential.label,
    )
    background_tasks.add_task(
        run_team_sync_background,
        org_id,
        body.team_id,
    )
    await _reload_scheduler(request)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="credential.generate",
        resource_type="credential",
        request=request,
        resource_id=created.credential.id,
        resource_name=created.credential.label,
    )
    return created


@router.get("/{credential_id}/secret", response_model=CredentialSecretResponse)
async def reveal_credential_secret(
    credential_id: UUID,
    current_user: User = Depends(require_permission("credentials", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialSecretResponse:
    org_id = require_operating_organization_id(scope)
    secret_value = await service.reveal_secret(
        org_id,
        credential_id,
    )
    return CredentialSecretResponse(secret_value=secret_value)


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: UUID,
    body: CredentialUpdateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("credentials", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> CredentialResponse:
    org_id = require_operating_organization_id(scope)
    updated = await service.update_credential(
        org_id,
        credential_id,
        body,
    )
    if body.secret_value:
        team_id = body.team_id or updated.team_id
        if team_id is not None:
            background_tasks.add_task(
                run_team_sync_background,
                org_id,
                team_id,
            )
    await _reload_scheduler(request)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="credential.update",
        resource_type="credential",
        request=request,
        resource_id=updated.id,
        resource_name=updated.label,
    )
    return updated


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_credential(
    credential_id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("credentials", "write")),
    scope: OperatingOrgScope = Depends(get_operating_org_scope),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    org_id = require_operating_organization_id(scope)
    await service.revoke_credential(org_id, credential_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="credential.delete",
        resource_type="credential",
        request=request,
        resource_id=credential_id,
    )
