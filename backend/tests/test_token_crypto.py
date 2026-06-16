"""Tests for token crypto helpers."""

from app.core.token_crypto import decrypt_token, encrypt_token, mask_token


def test_encrypt_decrypt_roundtrip() -> None:
    plain = "sk-test-token-abc123"
    cipher = encrypt_token(plain)
    assert cipher != plain
    assert decrypt_token(cipher) == plain


def test_mask_token() -> None:
    assert mask_token("sk-abcdefghij") == "****ghij"
