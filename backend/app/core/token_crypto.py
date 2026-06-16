"""Lightweight token encryption for collector credentials (dev MVP)."""

import base64
import hashlib

from app.config import get_settings


def _derive_key(raw: str) -> bytes:
    """Derive a 32-byte key from configured secret."""
    return hashlib.sha256(raw.encode("utf-8")).digest()


def encrypt_token(plain: str) -> str:
    """XOR-obfuscate token for at-rest storage (replace with KMS/Fernet in production)."""
    settings = get_settings()
    key = _derive_key(settings.collector_encryption_key)
    data = plain.encode("utf-8")
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode("ascii")


def decrypt_token(ciphertext: str) -> str:
    """Decrypt token stored by encrypt_token."""
    settings = get_settings()
    key = _derive_key(settings.collector_encryption_key)
    encrypted = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
    return plain.decode("utf-8")


def mask_token(plain: str) -> str:
    """Return masked representation for API responses."""
    if len(plain) <= 4:
        return "****"
    return f"****{plain[-4:]}"
