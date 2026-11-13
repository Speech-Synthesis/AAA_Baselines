"""
Unit Tests for Voiceprint Biometric Encryption (AES-256-GCM)
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

import unittest
import os
from app.security.voiceprint_crypto import (
    VoiceprintEncryptor,
    VoiceprintDecryptionError,
    derive_tenant_voiceprint_key,
)

class TestVoiceprintCrypto(unittest.TestCase):
    def setUp(self):
        self.key = os.urandom(32)
        self.encryptor = VoiceprintEncryptor(self.key)
        self.dummy_embedding = [0.1234, -0.5678, 0.9999, -0.0001] * 48  # 192 dimensions

    def test_encrypt_decrypt_exact_match(self):
        ciphertext, nonce = self.encryptor.encrypt(self.dummy_embedding)
        self.assertEqual(len(nonce), 12)
        self.assertNotEqual(ciphertext, self.dummy_embedding)

        decrypted = self.encryptor.decrypt(ciphertext, nonce)
        self.assertEqual(len(decrypted), 192)
        for original, restored in zip(self.dummy_embedding, decrypted):
            self.assertAlmostEqual(original, restored, places=4)

    def test_packed_format(self):
        packed = self.encryptor.encrypt_to_packed(self.dummy_embedding)
        decrypted = self.encryptor.decrypt_from_packed(packed)
        self.assertEqual(len(decrypted), 192)

    def test_tamper_detection(self):
        ciphertext, nonce = self.encryptor.encrypt(self.dummy_embedding)
        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 0xFF

        with self.assertRaises(VoiceprintDecryptionError):
            self.encryptor.decrypt(bytes(tampered_ciphertext), nonce)

    def test_wrong_key_fails_authentication(self):
        ciphertext, nonce = self.encryptor.encrypt(self.dummy_embedding)
        other_encryptor = VoiceprintEncryptor(os.urandom(32))

        with self.assertRaises(VoiceprintDecryptionError):
            other_encryptor.decrypt(ciphertext, nonce)

    def test_tenant_key_derivation(self):
        key_alpha = derive_tenant_voiceprint_key("bank-alpha", self.key)
        key_beta = derive_tenant_voiceprint_key("bank-beta", self.key)
        self.assertNotEqual(key_alpha, key_beta)
        self.assertEqual(len(key_alpha), 32)
        self.assertEqual(len(key_beta), 32)

if __name__ == "__main__":
    unittest.main()
