"""Live API token validation against vendor endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.admin.providers.provider_http import (
    ProviderRequestConfig,
    cursor_daily_usage_body,
    execute_provider_request,
)


@dataclass(frozen=True)
class ProviderValidationResult:
    valid: bool
    message: str
    status_code: int | None = None


# Known lightweight auth-check calls per provider slug.
_PROVIDER_CHECKS: dict[str, ProviderRequestConfig] = {
    "openai": ProviderRequestConfig(
        url="https://api.openai.com/v1/models",
        auth_mode="bearer",
    ),
    "anthropic": ProviderRequestConfig(
        url="https://api.anthropic.com/v1/models",
        auth_mode="anthropic",
    ),
    "google": ProviderRequestConfig(
        url="https://generativelanguage.googleapis.com/v1/models",
        auth_mode="google_query",
    ),
    "cohere": ProviderRequestConfig(
        url="https://api.cohere.com/v1/models",
        auth_mode="bearer",
    ),
    "mistral": ProviderRequestConfig(
        url="https://api.mistral.ai/v1/models",
        auth_mode="bearer",
    ),
    "cursor": ProviderRequestConfig(
        url="https://api.cursor.com/teams/members",
        auth_mode="basic",
    ),
}


async def validate_provider_token(
    *,
    provider_slug: str,
    api_key: str,
    usage_api_url: str,
    timeout_seconds: float = 15.0,
) -> ProviderValidationResult:
    """Validate an API token against the vendor's live API."""
    api_key = api_key.strip()
    if not api_key:
        return ProviderValidationResult(
            valid=False,
            message="API key is required.",
        )

    config = _PROVIDER_CHECKS.get(provider_slug)
    if config is None:
        config = ProviderRequestConfig(url=usage_api_url, auth_mode="bearer")

    if provider_slug == "cursor" and "daily-usage-data" in usage_api_url:
        config = ProviderRequestConfig(
            url=usage_api_url,
            method="POST",
            auth_mode="basic",
            json_body=cursor_daily_usage_body(days=1),
        )

    try:
        response = await execute_provider_request(
            api_key=api_key,
            config=config,
            usage_api_url=usage_api_url,
            timeout_seconds=timeout_seconds,
        )
    except ValueError as exc:
        return ProviderValidationResult(valid=False, message=str(exc))
    except httpx.TimeoutException:
        return ProviderValidationResult(
            valid=False,
            message="Timed out connecting to the provider. Check the URL and try again.",
        )
    except httpx.RequestError as exc:
        host = urlparse(config.url or usage_api_url).netloc or "provider"
        return ProviderValidationResult(
            valid=False,
            message=f"Could not reach {host}: {exc}",
        )

    if response.status_code in (401, 403):
        if provider_slug == "cursor":
            return ProviderValidationResult(
                valid=False,
                message=(
                    "Cursor API key is invalid or lacks team admin permissions. "
                    "Use a Team Admin API key from Cursor team settings."
                ),
                status_code=response.status_code,
            )
        return ProviderValidationResult(
            valid=False,
            message="API key is invalid or lacks permission for this provider.",
            status_code=response.status_code,
        )

    if response.status_code == 404 and provider_slug == "azure_openai":
        return ProviderValidationResult(
            valid=True,
            message=(
                "Connection accepted. Configure your Azure resource name in the "
                "provider usage URL before collecting usage."
            ),
            status_code=response.status_code,
        )

    if response.status_code >= 400:
        if provider_slug == "cursor":
            return ProviderValidationResult(
                valid=False,
                message=(
                    f"Cursor API rejected the request (HTTP {response.status_code}). "
                    "Ensure you are using a Team Admin API key and that the provider "
                    "usage URL is https://api.cursor.com/teams/daily-usage-data."
                ),
                status_code=response.status_code,
            )
        return ProviderValidationResult(
            valid=False,
            message=f"Provider rejected the request (HTTP {response.status_code}).",
            status_code=response.status_code,
        )

    provider_label = provider_slug.replace("_", " ").title()
    if provider_slug == "cursor":
        return ProviderValidationResult(
            valid=True,
            message="Cursor Team API key is valid.",
            status_code=response.status_code,
        )

    return ProviderValidationResult(
        valid=True,
        message=f"API key is valid for {provider_label}.",
        status_code=response.status_code,
    )
