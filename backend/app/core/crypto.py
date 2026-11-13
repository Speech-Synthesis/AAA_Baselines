"""
Bridge module exposing VoiceprintEncryptor to core.crypto.
"""
from ..security.voiceprint_crypto import (
    VoiceprintEncryptor,
    VoiceprintCryptoError,
    VoiceprintDecryptionError,
    derive_tenant_voiceprint_key,
)

__all__ = [
    "VoiceprintEncryptor",
    "VoiceprintCryptoError",
    "VoiceprintDecryptionError",
    "derive_tenant_voiceprint_key",
]
