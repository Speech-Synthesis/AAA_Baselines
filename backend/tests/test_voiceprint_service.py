"""
Tests for Voiceprint Service - Encryption/Decryption Integration
"""

import json

import pytest

from app.security.voiceprint_crypto import (
    VoiceprintDecryptionError,
    VoiceprintEncryptor,
)
from app.services.voiceprint_service import (
    decrypt_embedding,
    encrypt_embedding,
    get_encryptor,
    is_encrypted,
)


class TestVoiceprintService:
    """Tests for voiceprint service functions."""

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample 192-dim embedding."""
        return [0.1234, -0.5678, 0.9999, -0.0001] * 48

    def test_encrypt_embedding_returns_prefixed_string(self, sample_embedding):
        """Encrypted embedding should start with ENC: prefix."""
        encrypted = encrypt_embedding(sample_embedding)
        assert isinstance(encrypted, str)
        assert encrypted.startswith("ENC:")

    def test_encrypt_decrypt_roundtrip(self, sample_embedding):
        """Encryption and decryption should be lossless."""
        encrypted = encrypt_embedding(sample_embedding)
        decrypted = decrypt_embedding(encrypted)

        assert len(decrypted) == len(sample_embedding)
        for original, restored in zip(sample_embedding, decrypted, strict=True):
            assert abs(original - restored) < 1e-10

    def test_decrypt_legacy_list_format(self, sample_embedding):
        """Should handle legacy unencrypted list format."""
        decrypted = decrypt_embedding(sample_embedding)
        assert decrypted == sample_embedding

    def test_decrypt_legacy_json_string(self, sample_embedding):
        """Should handle legacy JSON string format."""
        json_str = json.dumps(sample_embedding)
        decrypted = decrypt_embedding(json_str)
        assert decrypted == sample_embedding

    def test_is_encrypted_true_for_encrypted(self, sample_embedding):
        """is_encrypted should return True for encrypted data."""
        encrypted = encrypt_embedding(sample_embedding)
        assert is_encrypted(encrypted) is True

    def test_is_encrypted_false_for_list(self, sample_embedding):
        """is_encrypted should return False for list data."""
        assert is_encrypted(sample_embedding) is False

    def test_is_encrypted_false_for_json(self, sample_embedding):
        """is_encrypted should return False for JSON string."""
        json_str = json.dumps(sample_embedding)
        assert is_encrypted(json_str) is False

    def test_encrypt_with_tenant_id(self, sample_embedding):
        """Encryption with tenant_id should use derived key."""
        encrypted_default = encrypt_embedding(sample_embedding)
        encrypted_tenant = encrypt_embedding(sample_embedding, tenant_id="tenant-123")

        # Different keys should produce different ciphertext
        # (can't directly compare due to random nonce, but they should both work)
        assert encrypted_default.startswith("ENC:")
        assert encrypted_tenant.startswith("ENC:")

        # Each should decrypt with same parameters
        decrypted = decrypt_embedding(encrypted_tenant, tenant_id="tenant-123")
        assert len(decrypted) == len(sample_embedding)

    def test_tenant_isolation(self, sample_embedding):
        """Data encrypted for one tenant should not decrypt for another."""
        encrypted = encrypt_embedding(sample_embedding, tenant_id="tenant-A")

        with pytest.raises(VoiceprintDecryptionError):
            decrypt_embedding(encrypted, tenant_id="tenant-B")

    def test_encrypt_with_user_id_aad(self, sample_embedding):
        """Encryption with user_id as AAD should bind to user."""
        user_id = "user-12345"
        encrypted = encrypt_embedding(sample_embedding, user_id=user_id)

        # Should decrypt with correct user_id
        decrypted = decrypt_embedding(encrypted, user_id=user_id)
        assert len(decrypted) == len(sample_embedding)

        # Should fail with wrong user_id (AAD mismatch)
        with pytest.raises(VoiceprintDecryptionError):
            decrypt_embedding(encrypted, user_id="wrong-user")

    def test_get_encryptor_default(self):
        """get_encryptor without tenant_id should return default encryptor."""
        encryptor = get_encryptor()
        assert isinstance(encryptor, VoiceprintEncryptor)

    def test_get_encryptor_tenant(self):
        """get_encryptor with tenant_id should return tenant-specific encryptor."""
        encryptor_a = get_encryptor("tenant-A")
        encryptor_b = get_encryptor("tenant-B")

        assert isinstance(encryptor_a, VoiceprintEncryptor)
        assert isinstance(encryptor_b, VoiceprintEncryptor)

        # Keys should be different
        assert encryptor_a.key != encryptor_b.key

    def test_decrypt_invalid_base64(self):
        """Should raise error for invalid base64."""
        with pytest.raises(VoiceprintDecryptionError):
            decrypt_embedding("ENC:invalid-base64!!!")

    def test_decrypt_truncated_data(self):
        """Should raise error for truncated encrypted data."""
        with pytest.raises(VoiceprintDecryptionError):
            decrypt_embedding("ENC:YWJjZGVm")  # Too short to be valid

    def test_decrypt_tampered_data(self, sample_embedding):
        """Should raise error for tampered ciphertext."""
        encrypted = encrypt_embedding(sample_embedding)

        # Tamper with the ciphertext (after ENC: prefix and nonce)
        import base64
        enc_part = encrypted[4:]  # Remove "ENC:"
        data = bytearray(base64.b64decode(enc_part))
        data[15] ^= 0xFF  # Flip a byte in ciphertext
        tampered = "ENC:" + base64.b64encode(bytes(data)).decode("ascii")

        with pytest.raises(VoiceprintDecryptionError):
            decrypt_embedding(tampered)


class TestVoiceprintServiceEnvironment:
    """Tests for voiceprint service environment variable handling."""

    def test_uses_voiceprint_key_env(self, sample_embedding, monkeypatch):
        """Should use VOICEPRINT_KEY environment variable."""
        monkeypatch.setenv("VOICEPRINT_KEY", "test-key-for-voiceprint-2024")

        # Need to get a fresh encryptor
        from app.services import voiceprint_service
        voiceprint_service._default_encryptor = None

        encrypted = encrypt_embedding(sample_embedding)
        decrypted = decrypt_embedding(encrypted)
        assert len(decrypted) == len(sample_embedding)

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample 192-dim embedding."""
        return [0.1234, -0.5678, 0.9999, -0.0001] * 48


class TestVoiceprintServiceEdgeCases:
    """Edge case tests for voiceprint service."""

    def test_empty_tenant_id_uses_default(self):
        """Empty tenant_id should use default encryptor (falsy check)."""
        # Empty string is falsy, so it uses default encryptor
        encryptor = get_encryptor("")
        default_encryptor = get_encryptor(None)
        # Both should return the same default encryptor
        assert encryptor is default_encryptor

    def test_encrypt_empty_embedding_raises(self):
        """Empty embedding should raise ValueError."""
        with pytest.raises(ValueError):
            encrypt_embedding([])

    def test_encrypt_non_list_raises(self):
        """Non-list embedding should raise ValueError."""
        with pytest.raises((ValueError, TypeError)):
            encrypt_embedding("not a list")  # type: ignore

    def test_decrypt_empty_string(self):
        """Empty string should raise error."""
        with pytest.raises((VoiceprintDecryptionError, json.JSONDecodeError)):
            decrypt_embedding("")

    def test_large_embedding(self):
        """Should handle larger-than-usual embeddings."""
        large_embedding = [0.1] * 1024  # 1024-dim
        encrypted = encrypt_embedding(large_embedding)
        decrypted = decrypt_embedding(encrypted)
        assert len(decrypted) == 1024
