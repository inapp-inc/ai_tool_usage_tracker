"""Structured logging for provider / tool HTTP calls."""

from __future__ import annotations

import logging

logger = logging.getLogger("app.integration.http")

MAX_BODY_LOG_CHARS = 4000


def truncate_body(text: str, limit: int = MAX_BODY_LOG_CHARS) -> str:
    cleaned = text.replace("\r\n", "\n").strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}… [truncated]"


def log_provider_http(
    *,
    operation: str,
    method: str,
    url: str,
    status_code: int,
    response_body: str = "",
    provider: str | None = None,
    tool_vendor: str | None = None,
    level: int | None = None,
) -> None:
    """Write provider API request outcome to application logs (visible in Docker api logs)."""
    resolved_level = level if level is not None else (logging.WARNING if status_code >= 400 else logging.INFO)
    logger.log(
        resolved_level,
        (
            "Provider API %s | operation=%s method=%s vendor=%s url=%s status=%s | response_body=%s"
        ),
        "error" if status_code >= 400 else "ok",
        operation,
        method,
        tool_vendor or provider or "-",
        url,
        status_code,
        truncate_body(response_body) if response_body else "(empty)",
    )
