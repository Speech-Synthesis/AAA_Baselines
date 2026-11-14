"""
AAA Engine - Voiceprint Service
Provides encrypted voiceprint storage and retrieval.
Wraps the low-level crypto module for use in the verification pipeline.
"""

import base64
import json
import logging

from ..security.voiceprint_crypto import (
    VoiceprintDecryptionError,
    VoiceprintEncryptor,
    derive_tenant_voiceprint_key,
)

logger = logging.getLogger(__name__)

# Module-level encryptor using default key
_default_encryptor: VoiceprintEncryptor | None = None


def get_encryptor(tenant_id: str | None = None) -> VoiceprintEncryptor:
    """
    Get a VoiceprintEncryptor instance.

    If tenant_id is provided, derives a tenant-specific key for isolation.
    Otherwise, uses the default shared key.
    """
    global _default_encryptor

    if tenant_id:
        # Derive tenant-specific key for multi-tenant isolation
        tenant_key = derive_tenant_voiceprint_key(tenant_id)
        return VoiceprintEncryptor(tenant_key)

    # Use default encryptor (lazy initialization)
    if _default_encryptor is None:
        _default_encryptor = VoiceprintEncryptor()

    return _default_encryptor


def encrypt_embedding(
    embedding: list[float],
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> str:
    """
    Encrypt a voiceprint embedding for storage.

    Args:
        embedding: 192-dimensional float embedding
        tenant_id: Optional tenant ID for key derivation
        user_id: Optional user ID for associated data binding

    Returns:
        Base64-encoded encrypted blob (prefixed with 'ENC:' marker)
    """
    encryptor = get_encryptor(tenant_id)

    # Use user_id as associated data if provided (binds ciphertext to user)
    associated_data = user_id.encode() if user_id else None

    # Encrypt to packed format (nonce + ciphertext)
    packed = encryptor.encrypt_to_packed(embedding, associated_data)

    # Encode as base64 with marker prefix
    encoded = base64.b64encode(packed).decode("ascii")
    return f"ENC:{encoded}"


def decrypt_embedding(
    stored_value: str | list[float],
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> list[float]:
    """
    Decrypt a stored voiceprint embedding.

    Handles both encrypted (ENC: prefixed) and legacy unencrypted formats.

    Args:
        stored_value: Either encrypted string or raw embedding list
        tenant_id: Optional tenant ID for key derivation
        user_id: Optional user ID for associated data verification

    Returns:
        Decrypted 192-dimensional float embedding

    Raises:
        VoiceprintDecryptionError: If decryption fails
    """
    # Already decrypted (legacy format)
    if isinstance(stored_value, list):
        return stored_value

    # Check for encryption marker
    if not stored_value.startswith("ENC:"):
        # Legacy JSON format - try to parse
        try:
            return json.loads(stored_value)
        except (json.JSONDecodeError, TypeError) as e:
            raise VoiceprintDecryptionError(f"Invalid embedding format: {e}") from e

    # Encrypted format
    encryptor = get_encryptor(tenant_id)

    # Remove marker and decode base64
    encoded = stored_value[4:]  # Strip "ENC:"
    try:
        packed = base64.b64decode(encoded)
    except Exception as e:
        raise VoiceprintDecryptionError(f"Invalid base64 encoding: {e}") from e

    # Use user_id as associated data if provided
    associated_data = user_id.encode() if user_id else None

    return encryptor.decrypt_from_packed(packed, associated_data)


def is_encrypted(stored_value: str | list[float]) -> bool:
    """Check if a stored embedding is in encrypted format."""
    if isinstance(stored_value, list):
        return False
    return stored_value.startswith("ENC:")
