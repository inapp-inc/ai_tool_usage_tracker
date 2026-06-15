"""Unit tests for credential encryption."""

from app.core.encryption import decrypt_secret, encrypt_secret, mask_secret


def test_encrypt_decrypt_roundtrip() -> None:
    key = "test_encryption_key_material"
    plaintext = "sk-proj-abc123secret"
    ciphertext = encrypt_secret(plaintext, key)
    assert ciphertext != plaintext.encode()
    assert decrypt_secret(ciphertext, key) == plaintext


def test_mask_secret() -> None:
    assert mask_secret("sk-proj-abcd") == "****abcd"
    assert mask_secret("ab") == "****ab"
