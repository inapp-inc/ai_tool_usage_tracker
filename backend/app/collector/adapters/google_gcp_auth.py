"""GCP service-account auth for Google Cloud Monitoring (Gemini usage)."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
import jwt

MONITORING_READ_SCOPE = "https://www.googleapis.com/auth/monitoring.read"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def parse_service_account_json(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text.startswith("{"):
            msg = "GCP service account JSON must be an object or JSON string."
            raise ValueError(msg)
        data = json.loads(text)
    else:
        msg = "GCP service account JSON must be an object or JSON string."
        raise ValueError(msg)

    if data.get("type") != "service_account":
        msg = "GCP credentials must be a service account JSON key (type=service_account)."
        raise ValueError(msg)
    for field in ("client_email", "private_key", "project_id"):
        if not str(data.get(field) or "").strip():
            msg = f"GCP service account JSON is missing required field: {field}"
            raise ValueError(msg)
    return data


def _build_jwt(service_account: dict[str, Any], *, scopes: list[str]) -> str:
    now = int(time.time())
    payload = {
        "iss": service_account["client_email"],
        "sub": service_account["client_email"],
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
        "scope": " ".join(scopes),
    }
    return jwt.encode(payload, service_account["private_key"], algorithm="RS256")


async def fetch_gcp_access_token(
    service_account: dict[str, Any],
    *,
    scopes: list[str] | None = None,
) -> str:
    scope_list = scopes or [MONITORING_READ_SCOPE]
    assertion = _build_jwt(service_account, scopes=scope_list)
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
    if response.status_code >= 400:
        msg = f"GCP access token request failed (HTTP {response.status_code})."
        raise RuntimeError(msg)
    payload = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        msg = "GCP access token response did not include access_token."
        raise RuntimeError(msg)
    return token
