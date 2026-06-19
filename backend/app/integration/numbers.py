"""Parse numeric strings including compact K/M suffixes (e.g. 15K → 15000)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

_COMPACT_SUFFIX = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([KkMm])?\s*$")


def parse_compact_int(value: Any, default: int = 0) -> int:
    """Parse integers from plain numbers or compact suffixes (K × 1_000, M × 1_000_000)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return max(value, 0) if default >= 0 else value
    if isinstance(value, float):
        parsed = int(value)
        return max(parsed, 0) if default >= 0 and parsed < 0 else parsed

    text = str(value).strip().replace(",", "")
    if not text:
        return default

    match = _COMPACT_SUFFIX.match(text)
    if match:
        number = Decimal(match.group(1))
        suffix = (match.group(2) or "").upper()
        if suffix == "K":
            number *= Decimal("1000")
        elif suffix == "M":
            number *= Decimal("1000000")
        parsed = int(number)
        return max(parsed, 0) if default >= 0 and parsed < 0 else parsed

    try:
        parsed = int(Decimal(text))
        return max(parsed, 0) if default >= 0 and parsed < 0 else parsed
    except InvalidOperation:
        pass

    try:
        parsed = int(float(text))
        return max(parsed, 0) if default >= 0 and parsed < 0 else parsed
    except ValueError:
        return default
