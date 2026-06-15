"""Unit tests for refresh token hashing."""

from app.auth.repositories.refresh_token import RefreshTokenRepository
from app.core.security import generate_opaque_refresh_token, hash_refresh_token


def test_refresh_token_hash_only_in_repository() -> None:
    plain = generate_opaque_refresh_token()
    stored = RefreshTokenRepository.store_hash(plain)
    assert stored == hash_refresh_token(plain)
    assert stored != plain
    assert len(stored) == 64
