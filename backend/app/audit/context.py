"""Request metadata helpers for audit logging."""

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_correlation_id(request: Request) -> str | None:
    return request.headers.get("X-Correlation-ID")
