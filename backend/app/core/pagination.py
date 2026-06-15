"""Opaque cursor pagination (keyset) for list endpoints."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any


class CursorError(ValueError):
    """Invalid or tampered pagination cursor."""


def encode_cursor(**parts: str) -> str:
    """Encode cursor parts as URL-safe base64 JSON."""
    payload = json.dumps(parts, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> dict[str, str]:
    """Decode an opaque cursor to its key/value parts."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise CursorError("Cursor payload must be an object")
        return {str(key): str(value) for key, value in data.items()}
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise CursorError("Invalid pagination cursor") from exc


@dataclass(frozen=True)
class PageMeta:
    """Pagination metadata returned with list responses."""

    limit: int
    next_cursor: str | None
    has_more: bool


def build_page_meta(
    items: list[Any],
    limit: int,
    *,
    next_cursor: str | None,
) -> PageMeta:
    has_more = len(items) > limit
    if has_more:
        items = items[:limit]
    return PageMeta(
        limit=limit,
        next_cursor=next_cursor if has_more else None,
        has_more=has_more,
    )
