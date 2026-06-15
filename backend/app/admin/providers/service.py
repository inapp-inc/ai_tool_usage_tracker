"""Provider registry business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.providers.defaults import DEFAULT_PROVIDERS
from app.admin.providers.repository import ProviderRepository
from app.admin.providers.schemas import (
    PaginationMeta,
    ProviderCreateRequest,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdateRequest,
    ValidateProviderRequest,
    ValidateProviderResponse,
)
from app.auth.service import AuthenticatedUser
from app.core.pagination import CursorError
from app.models.admin import Provider
from app.admin.providers.validator import validate_provider_token as run_token_validation


class ProviderConflictError(Exception):
    """Provider slug already exists."""


class ProviderNotFoundError(Exception):
    """Provider not found."""


class ProviderInUseError(Exception):
    """Provider is referenced by tools."""


class ProviderProtectedError(Exception):
    """System provider cannot be deleted."""


class ProviderValidationError(Exception):
    """Provider validation request is invalid."""


class ProviderService:
    """Provider CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._providers = ProviderRepository(session)

    def _to_response(self, provider: Provider) -> ProviderResponse:
        return ProviderResponse(
            id=provider.id,
            organization_id=provider.organization_id,
            slug=provider.slug,
            name=provider.name,
            usage_api_url=provider.usage_api_url,
            description=provider.description,
            is_system=provider.is_system,
            active=provider.active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    async def ensure_defaults(self, organization_id: uuid.UUID) -> None:
        """Seed built-in providers when an org has none."""
        if await self._providers.count_by_slug(organization_id, "openai") > 0:
            return

        for row in DEFAULT_PROVIDERS:
            provider = Provider(
                organization_id=organization_id,
                slug=str(row["slug"]),
                name=str(row["name"]),
                usage_api_url=str(row["usage_api_url"]),
                description=str(row["description"]) if row.get("description") else None,
                is_system=bool(row.get("is_system", False)),
                active=True,
            )
            await self._providers.add(provider)
        await self._session.commit()

    async def list_providers(
        self,
        user: AuthenticatedUser,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> ProviderListResponse:
        await self.ensure_defaults(user.organization_id)
        rows, next_cursor = await self._providers.list_providers(
            user.organization_id,
            active=active,
            limit=limit,
            cursor=cursor,
        )
        return ProviderListResponse(
            data=[self._to_response(row) for row in rows],
            meta=PaginationMeta(
                limit=limit,
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            ),
        )

    async def get_provider(
        self, user: AuthenticatedUser, provider_id: uuid.UUID
    ) -> ProviderResponse:
        provider = await self._providers.get_by_id(user.organization_id, provider_id)
        if provider is None:
            raise ProviderNotFoundError
        return self._to_response(provider)

    async def create_provider(
        self, user: AuthenticatedUser, body: ProviderCreateRequest
    ) -> ProviderResponse:
        existing = await self._providers.get_by_slug(user.organization_id, body.slug)
        if existing is not None:
            raise ProviderConflictError

        provider = Provider(
            organization_id=user.organization_id,
            slug=body.slug,
            name=body.name.strip(),
            usage_api_url=body.usage_api_url,
            description=body.description,
            is_system=False,
            active=True,
        )
        try:
            await self._providers.add(provider)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ProviderConflictError from exc
        await self._session.refresh(provider)
        return self._to_response(provider)

    async def update_provider(
        self,
        user: AuthenticatedUser,
        provider_id: uuid.UUID,
        body: ProviderUpdateRequest,
    ) -> ProviderResponse:
        provider = await self._providers.get_by_id(user.organization_id, provider_id)
        if provider is None:
            raise ProviderNotFoundError

        updates = body.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()

        for field, value in updates.items():
            setattr(provider, field, value)
        provider.updated_at = datetime.now(UTC)

        await self._providers.save(provider)
        await self._session.commit()
        await self._session.refresh(provider)
        return self._to_response(provider)

    async def delete_provider(
        self, user: AuthenticatedUser, provider_id: uuid.UUID
    ) -> None:
        provider = await self._providers.get_by_id(user.organization_id, provider_id)
        if provider is None:
            raise ProviderNotFoundError
        if provider.is_system:
            raise ProviderProtectedError

        tool_count = await self._providers.count_tools_using_vendor(
            user.organization_id, provider.slug
        )
        if tool_count > 0:
            raise ProviderInUseError

        await self._providers.delete(provider)
        await self._session.commit()

    async def validate_token(
        self, user: AuthenticatedUser, body: ValidateProviderRequest
    ) -> ValidateProviderResponse:
        slug = body.provider_slug.strip().lower()
        provider = await self._providers.get_by_slug(user.organization_id, slug)
        if provider is None:
            raise ProviderNotFoundError
        if not provider.active:
            raise ProviderValidationError("Provider is inactive.")

        result = await run_token_validation(
            provider_slug=provider.slug,
            api_key=body.api_token,
            usage_api_url=provider.usage_api_url,
        )
        return ValidateProviderResponse(
            valid=result.valid,
            message=result.message,
            status_code=result.status_code,
        )
