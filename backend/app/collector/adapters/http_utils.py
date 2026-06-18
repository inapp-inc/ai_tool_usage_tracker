"""HTTP helpers with response body capture for provider integrations."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class HttpResult:
    status_code: int
    text: str
    json: dict | list | None


def _parse_json(response: httpx.Response) -> dict | list | None:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


async def get_with_detail(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str | int] | None = None,
    timeout: float = 20.0,
) -> HttpResult:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url, headers=headers, params=params)
        return HttpResult(
            status_code=response.status_code,
            text=response.text,
            json=_parse_json(response),
        )


async def post_with_detail(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict | None = None,
    timeout: float = 20.0,
) -> HttpResult:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=json_body)
        return HttpResult(
            status_code=response.status_code,
            text=response.text,
            json=_parse_json(response),
        )


async def get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str | int] | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict | list | None]:
    result = await get_with_detail(url, headers=headers, params=params, timeout=timeout)
    return result.status_code, result.json


async def get_text(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> tuple[int, str]:
    result = await get_with_detail(url, headers=headers, timeout=timeout)
    return result.status_code, result.text


async def post_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict | list | None]:
    result = await post_with_detail(url, headers=headers, json_body=json_body, timeout=timeout)
    return result.status_code, result.json
