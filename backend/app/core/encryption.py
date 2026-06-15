"""AES-256-GCM encryption for vendor API credentials (NFR-SEC-001)."""

from __future__ import annotations

import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _derive_key(key_material: str) -> bytes:
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def encrypt_secret(plaintext: str, key_material: str) -> bytes:
    """Encrypt a secret; returns nonce + ciphertext bytes for BYTEA storage."""
    key = _derive_key(key_material)
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext


def decrypt_secret(ciphertext: bytes, key_material: str) -> str:
    """Decrypt a stored secret (internal use only — never exposed via API)."""
    key = _derive_key(key_material)
    nonce, encrypted = ciphertext[:12], ciphertext[12:]
    return AESGCM(key).decrypt(nonce, encrypted, None).decode("utf-8")


def mask_secret(secret: str) -> str:
    """Return masked display value per OpenAPI Credential.masked_secret."""
    suffix = secret[-4:] if len(secret) >= 4 else secret
    return f"****{suffix}"
