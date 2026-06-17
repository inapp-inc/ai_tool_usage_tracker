"""Credentials REST API — tool-backed API keys."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.router import get_audit_recorder, record_audit_event
from app.audit.recorder import AuditRecorder

from app.auth.dependencies import get_current_user
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
from app.tools.background import run_tool_sync_background

router = APIRouter(prefix="/credentials", tags=["Credentials"])

ADMIN_ROLES = frozenset({"super_admin"})


def get_credential_service(session: AsyncSession = Depends(get_session)) -> CredentialService:
    return CredentialService(session)


def require_credential_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


async def _reload_scheduler(request: Request) -> None:
    scheduler = getattr(request.app.state, "collector_scheduler", None)
    if scheduler is not None:
        await scheduler.reload()


@router.post("/validate", response_model=CredentialValidateResponse)
async def validate_credential(
    body: CredentialValidateRequest,
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialValidateResponse:
    return await service.validate_credential(current_user.organization_id, body)


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialListResponse:
    return await service.list_credentials(current_user.organization_id)


@router.post("", response_model=CredentialCreateResponseBody, status_code=status.HTTP_201_CREATED)
async def create_credential(
    body: CredentialCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> CredentialCreateResponseBody:
    created = await service.create_credential(current_user.organization_id, body)
    background_tasks.add_task(
        run_tool_sync_background,
        current_user.organization_id,
        created.credential.id,
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
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialSecretResponse:
    secret_value = await service.reveal_secret(
        current_user.organization_id,
        credential_id,
    )
    return CredentialSecretResponse(secret_value=secret_value)


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: UUID,
    body: CredentialUpdateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> CredentialResponse:
    updated = await service.update_credential(
        current_user.organization_id,
        credential_id,
        body,
    )
    if body.secret_value:
        background_tasks.add_task(
            run_tool_sync_background,
            current_user.organization_id,
            updated.id,
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
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
    recorder: AuditRecorder = Depends(get_audit_recorder),
) -> None:
    await service.revoke_credential(current_user.organization_id, credential_id)
    await record_audit_event(
        recorder,
        actor=current_user,
        action="credential.revoke",
        resource_type="credential",
        request=request,
        resource_id=credential_id,
    )
