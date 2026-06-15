"""API credential management (FR-ADM-003)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.credentials.repository import CredentialRepository
from app.admin.credentials.schemas import (
    CredentialCreateRequest,
    CredentialResponse,
    CredentialRotateRequest,
    CredentialUpdateRequest,
)
from app.admin.tools.repository import ToolRepository
from app.auth.service import AuthenticatedUser
from app.config import Settings, get_settings
from app.core.encryption import encrypt_secret
from app.core.pagination import CursorError
from app.models.admin import Credential


class CredentialNotFoundError(Exception):
    """Credential not found."""


class CredentialValidationError(Exception):
    """Invalid credential reference."""


class CredentialService:
    """Credential CRUD with encrypted storage."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._credentials = CredentialRepository(session)
        self._tools = ToolRepository(session)

    def _to_response(self, row: Credential) -> CredentialResponse:
        return CredentialResponse(
            id=row.id,
            tool_id=row.tool_id,
            team_id=row.team_id,
            environment=row.environment,  # type: ignore[arg-type]
            masked_secret=f"****{row.secret_last_four}",
            label=row.label,
            description=row.description,
            status=row.status,  # type: ignore[arg-type]
            rotation_reminder_days=row.rotation_reminder_days,
            expires_at=row.expires_at,
            last_rotated_at=row.last_rotated_at,
            created_at=row.created_at,
        )

    async def list_credentials(
        self,
        user: AuthenticatedUser,
        *,
        tool_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        rows, next_cursor = await self._credentials.list_credentials(
            user.organization_id,
            tool_id=tool_id,
            team_id=team_id,
            limit=limit,
            cursor=cursor,
        )
        return {
            "data": [self._to_response(row) for row in rows],
            "meta": {
                "limit": limit,
                "next_cursor": next_cursor,
                "has_more": next_cursor is not None,
            },
        }

    async def create_credential(
        self,
        user: AuthenticatedUser,
        body: CredentialCreateRequest,
    ) -> CredentialResponse:
        tool = await self._tools.get_by_id(user.organization_id, body.tool_id)
        if tool is None:
            raise CredentialValidationError("Tool not found.")

        secret = body.secret_value
        last_four = secret[-4:] if len(secret) >= 4 else secret
        ciphertext = encrypt_secret(
            secret, self._settings.credential_encryption_key
        )

        row = Credential(
            organization_id=user.organization_id,
            tool_id=body.tool_id,
            team_id=body.team_id,
            environment=body.environment,
            secret_ciphertext=ciphertext,
            secret_last_four=last_four,
            label=body.label,
            description=body.description,
            rotation_reminder_days=body.rotation_reminder_days,
            expires_at=body.expires_at,
            created_by=user.id,
        )
        await self._credentials.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def rotate_credential(
        self,
        user: AuthenticatedUser,
        credential_id: uuid.UUID,
        body: CredentialRotateRequest,
    ) -> CredentialResponse:
        row = await self._credentials.get_by_id(user.organization_id, credential_id)
        if row is None:
            raise CredentialNotFoundError

        secret = body.secret_value
        row.secret_ciphertext = encrypt_secret(
            secret, self._settings.credential_encryption_key
        )
        row.secret_last_four = secret[-4:] if len(secret) >= 4 else secret
        row.last_rotated_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        await self._credentials.save(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def delete_credential(
        self,
        user: AuthenticatedUser,
        credential_id: uuid.UUID,
    ) -> None:
        row = await self._credentials.get_by_id(user.organization_id, credential_id)
        if row is None:
            raise CredentialNotFoundError
        row.deleted_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        await self._credentials.save(row)
        await self._session.commit()

    async def update_credential(
        self,
        user: AuthenticatedUser,
        credential_id: uuid.UUID,
        body: CredentialUpdateRequest,
    ) -> CredentialResponse:
        row = await self._credentials.get_by_id(user.organization_id, credential_id)
        if row is None:
            raise CredentialNotFoundError

        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        row.updated_at = datetime.now(UTC)
        await self._credentials.save(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def revoke_credential(
        self,
        user: AuthenticatedUser,
        credential_id: uuid.UUID,
    ) -> CredentialResponse:
        row = await self._credentials.get_by_id(user.organization_id, credential_id)
        if row is None:
            raise CredentialNotFoundError
        row.status = "inactive"
        row.updated_at = datetime.now(UTC)
        await self._credentials.save(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)
