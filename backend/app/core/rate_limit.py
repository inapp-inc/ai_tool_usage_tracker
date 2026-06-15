"""Redis-backed login rate limiting."""

from __future__ import annotations

import hashlib

import redis.asyncio as redis

from app.config import Settings, get_settings


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()[:16]


def login_rate_limit_key(client_ip: str, email: str) -> str:
    """Build Redis key for login attempt tracking."""
    return f"login_attempts:{client_ip}:{_email_hash(email)}"


class LoginRateLimiter:
    """Sliding window rate limiter for failed login attempts."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._redis: redis.Redis | None = None

    async def _client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(
                str(self._settings.redis_url),
                decode_responses=True,
            )
        return self._redis

    async def is_blocked(self, client_ip: str, email: str) -> bool:
        """Return True if login attempts exceed threshold."""
        client = await self._client()
        key = login_rate_limit_key(client_ip, email)
        attempts = await client.get(key)
        if attempts is None:
            return False
        return int(attempts) >= self._settings.login_rate_limit_max_attempts

    async def record_failure(self, client_ip: str, email: str) -> None:
        """Increment failed login counter."""
        client = await self._client()
        key = login_rate_limit_key(client_ip, email)
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self._settings.login_rate_limit_window_seconds)
        await pipe.execute()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
