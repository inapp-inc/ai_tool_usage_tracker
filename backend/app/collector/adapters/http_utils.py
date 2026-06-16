"""Shared HTTP helpers for provider adapters."""

from __future__ import annotations

import httpx


async def get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str | int] | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict | list | None]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers, params=params)
        if response.content:
            try:
                return response.status_code, response.json()
            except ValueError:
                return response.status_code, None
        return response.status_code, None


async def post_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict | list | None]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=json_body)
        if response.content:
            try:
                return response.status_code, response.json()
            except ValueError:
                return response.status_code, None
        return response.status_code, None
