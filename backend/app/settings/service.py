"""Settings business logic."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Provider
from app.settings.repository import ProviderRepository
from app.settings.parent_repository import ProviderParentRepository
from app.settings.schemas import (
    ProviderCreateRequest,
    ProviderListResponse,
    ProviderParentListResponse,
    ProviderParentResponse,
    ProviderResponse,
    ProviderUpdateRequest,
)


class ProviderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._providers = ProviderRepository(session)
        self._parents = ProviderParentRepository(session)

    async def list_provider_parents(self) -> ProviderParentListResponse:
        rows = await self._parents.list_parents()
        return ProviderParentListResponse(
            data=[
                ProviderParentResponse(
                    slug=row.slug,
                    label=row.label,
                    sort_order=row.sort_order,
                )
                for row in rows
            ]
        )

    async def list_providers(self, *, active: bool | None = None) -> ProviderListResponse:
        rows = await self._providers.list_providers(active=active)
        return ProviderListResponse(data=[self._to_response(row) for row in rows])

    async def get_active_provider(self, slug: str) -> Provider:
        provider = await self._providers.get_by_slug(slug)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown provider: {slug}",
            )
        if not provider.active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Provider '{slug}' is inactive.",
            )
        return provider

    async def create_provider(self, body: ProviderCreateRequest) -> ProviderResponse:
        existing = await self._providers.get_by_slug(body.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Provider slug '{body.slug}' already exists.",
            )

        provider = await self._providers.create(
            slug=body.slug,
            label=body.label,
            description=body.description,
            logo_url=body.logo_url,
            sort_order=body.sort_order,
        )
        await self._session.commit()
        await self._session.refresh(provider)
        return self._to_response(provider)

    async def update_provider(
        self,
        slug: str,
        body: ProviderUpdateRequest,
    ) -> ProviderResponse:
        provider = await self._require_provider(slug)
        updates = body.model_fields_set

        if "label" in updates and body.label is not None:
            provider.label = body.label.strip()
        if "description" in updates:
            provider.description = body.description.strip() if body.description else None
        if "logo_url" in updates:
            provider.logo_url = body.logo_url.strip() if body.logo_url else None
        if "active" in updates and body.active is not None:
            provider.active = body.active
        if "sort_order" in updates and body.sort_order is not None:
            provider.sort_order = body.sort_order

        await self._session.commit()
        await self._session.refresh(provider)
        return self._to_response(provider)

    async def delete_provider(self, slug: str) -> None:
        provider = await self._require_provider(slug)
        if provider.built_in:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Built-in providers cannot be deleted.",
            )
        await self._providers.delete(provider)
        await self._session.commit()

    async def _require_provider(self, slug: str) -> Provider:
        provider = await self._providers.get_by_slug(slug)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found.",
            )
        return provider

    @staticmethod
    def _to_response(provider: Provider) -> ProviderResponse:
        parent = provider.parent
        return ProviderResponse(
            slug=provider.slug,
            label=provider.label,
            description=provider.description,
            logo_url=provider.logo_url,
            parent_slug=provider.parent_slug,
            parent_label=parent.label if parent is not None else None,
            adapter_key=provider.adapter_key,
            requires_api_endpoint=bool(provider.requires_api_endpoint),
            built_in=provider.built_in,
            active=provider.active,
            sort_order=provider.sort_order,
        )
