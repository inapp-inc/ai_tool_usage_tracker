"""Application logging — ensures app.* loggers appear in Docker stdout."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure root and app loggers once (uvicorn does not set these by default)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    numeric = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(
        fmt="%(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(numeric)
    if not root.handlers:
        root.addHandler(handler)
    else:
        for existing in root.handlers:
            existing.setFormatter(formatter)

    for name in (
        "app",
        "app.integration.http",
        "app.credentials",
        "app.tools",
        "app.teams",
        "app.collector",
    ):
        logging.getLogger(name).setLevel(numeric)

    _CONFIGURED = True
