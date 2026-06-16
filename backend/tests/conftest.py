"""Pytest configuration for backend tests."""

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitracker:test@localhost:5432/aitracker",
)
os.environ.setdefault("COLLECTOR_ENCRYPTION_KEY", "test_collector_encryption_key")
