"""
AAA Engine - Voiceprint Biometric Encryption Module
Target 4: AES-256-GCM authenticated encryption for voice embeddings at rest.

Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
Role: Security & Perimeter Defense Engineer
"""

import os
import json
import hmac
import hashlib
from typing import List, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE_BYTES = 12  # Standard 96-bit nonce for AES-GCM
KEY_SIZE_BYTES = 32    # 256-bit AES key


class VoiceprintCryptoError(Exception):
    """Base exception for voiceprint encryption failures."""
    pass


class VoiceprintDecryptionError(VoiceprintCryptoError):
    """Raised when ciphertext authentication or integrity check fails."""
    pass


class VoiceprintEncryptor:
    """
    AES-256-GCM encryptor for biometric voiceprint embeddings.
    Provides authenticated encryption with associated data (AEAD).
    """

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            raw_key = os.environ.get("VOICEPRINT_KEY") or os.environ.get("SECRET_KEY") or "aaa-default-voiceprint-key-32ch!!"
            self.key = hashlib.sha256(raw_key.encode() if isinstance(raw_key, str) else raw_key).digest()
        else:
            if len(key) != KEY_SIZE_BYTES:
                raise ValueError(f"AES-256 key must be exactly {KEY_SIZE_BYTES} bytes, got {len(key)}")
            self.key = key

        self._aesgcm = AESGCM(self.key)

    def encrypt(self, embedding: List[float], associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypts a 192-dimensional float embedding using AES-256-GCM.
        
        Returns:
            Tuple[bytes, bytes]: (ciphertext, 12-byte random nonce)
        """
        if not embedding or not isinstance(embedding, list):
            raise ValueError("Embedding must be a non-empty list of floats")

        nonce = os.urandom(NONCE_SIZE_BYTES)
        data = json.dumps(embedding).encode("utf-8")
        ciphertext = self._aesgcm.encrypt(nonce, data, associated_data)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes, associated_data: Optional[bytes] = None) -> List[float]:
        """
        Decrypts and verifies an authenticated voiceprint embedding.
        
        Raises:
            VoiceprintDecryptionError: If ciphertext was tampered with or key is invalid.
        """
        if len(nonce) != NONCE_SIZE_BYTES:
            raise VoiceprintDecryptionError(f"Invalid nonce length: expected {NONCE_SIZE_BYTES}, got {len(nonce)}")

        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, associated_data)
            return json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            raise VoiceprintDecryptionError(f"Decryption failed: data corrupted or key mismatch ({str(e)})")
