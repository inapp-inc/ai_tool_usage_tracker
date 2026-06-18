"""Build HTTP headers from integration auth config."""

from __future__ import annotations


def build_auth_headers(
    auth_config: dict | None,
    api_token: str,
    extra_headers: dict | None = None,
) -> dict[str, str]:
    auth = auth_config or {}
    auth_type = str(auth.get("type") or "bearer").lower()
    header_name = str(auth.get("header") or "Authorization")
    prefix = str(auth.get("prefix") or "")

    headers: dict[str, str] = {}
    if extra_headers:
        for key, value in extra_headers.items():
            if value is not None:
                headers[str(key)] = str(value)

    token = api_token.strip()
    if auth_type == "api_key_header":
        headers[header_name] = token
    elif auth_type == "basic":
        headers[header_name] = f"Basic {token}" if not token.startswith("Basic ") else token
    else:
        if prefix and not token.startswith(prefix.strip()):
            headers[header_name] = f"{prefix}{token}"
        else:
            headers[header_name] = token if prefix else f"Bearer {token}"

    return headers
