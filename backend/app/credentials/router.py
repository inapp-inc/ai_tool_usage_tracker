"""Credentials REST API — tool-backed API keys."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.credentials.schemas import (
    CredentialCreateRequest,
    CredentialCreateResponseBody,
    CredentialListResponse,
    CredentialResponse,
    CredentialSecretResponse,
    CredentialUpdateRequest,
)
from app.credentials.service import CredentialService
from app.db.session import get_session
from app.models.auth import User

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


@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialListResponse:
    return await service.list_credentials(current_user.organization_id)


@router.post("", response_model=CredentialCreateResponseBody, status_code=status.HTTP_201_CREATED)
async def create_credential(
    body: CredentialCreateRequest,
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialCreateResponseBody:
    return await service.create_credential(current_user.organization_id, body)


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
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> CredentialResponse:
    return await service.update_credential(
        current_user.organization_id,
        credential_id,
        body,
    )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_credential(
    credential_id: UUID,
    current_user: User = Depends(require_credential_admin),
    service: CredentialService = Depends(get_credential_service),
) -> None:
    await service.revoke_credential(current_user.organization_id, credential_id)
