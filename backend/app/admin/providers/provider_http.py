"""Shared HTTP client settings for vendor provider APIs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx

AuthMode = Literal["bearer", "basic", "anthropic", "google_query"]


@dataclass(frozen=True)
class ProviderRequestConfig:
    url: str
    method: str = "GET"
    auth_mode: AuthMode = "bearer"
    json_body: dict | str | None = None


def anthropic_headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }


def google_url(base_url: str, api_key: str) -> str:
    joiner = "&" if "?" in base_url else "?"
    return f"{base_url}{joiner}key={api_key}"


def cursor_daily_usage_body(*, days: int = 30) -> dict[str, int]:
    end = datetime.now(tz=UTC)
    start = end - timedelta(days=min(max(days, 1), 30))
    return {
        "startDate": int(start.timestamp() * 1000),
        "endDate": int(end.timestamp() * 1000),
    }


def build_provider_request(
    *,
    api_key: str,
    config: ProviderRequestConfig,
    usage_api_url: str = "",
) -> tuple[str, str, dict[str, str], httpx.Auth | None, dict | str | None]:
    if config.auth_mode == "google_query":
        return (
            config.method,
            google_url(config.url, api_key),
            {},
            None,
            config.json_body,
        )

    if config.auth_mode == "basic":
        return (
            config.method,
            config.url,
            {"Content-Type": "application/json"},
            httpx.BasicAuth(api_key, ""),
            config.json_body,
        )

    if config.auth_mode == "anthropic":
        return (
            config.method,
            config.url,
            anthropic_headers(api_key),
            None,
            config.json_body,
        )

    request_url = (config.url or usage_api_url).strip()
    if not request_url.startswith(("http://", "https://")):
        raise ValueError("Provider usage API URL is not configured.")

    return (
        config.method,
        request_url,
        {"Authorization": f"Bearer {api_key}"},
        None,
        config.json_body,
    )


async def execute_provider_request(
    *,
    api_key: str,
    config: ProviderRequestConfig,
    usage_api_url: str = "",
    timeout_seconds: float = 30.0,
) -> httpx.Response:
    method, request_url, headers, auth, json_body = build_provider_request(
        api_key=api_key,
        config=config,
        usage_api_url=usage_api_url,
    )
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
        return await client.request(
            method,
            request_url,
            headers=headers,
            auth=auth,
            json=json_body if method.upper() == "POST" else None,
        )
