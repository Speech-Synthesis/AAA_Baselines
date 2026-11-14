"""
Unit and Integration Tests for AAA Engine Security & JWT Authentication
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

import os
import unittest

from fastapi import FastAPI, HTTPException, status
from jose import jwt

from app.security.jwt_auth import (
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_SECRET,
    TokenRequest,
    configure_cors,
    create_tenant_token,
    enforce_lockout_policy,
    enforce_rate_limit,
    exchange_token,
    get_current_tenant,
    record_auth_failure,
    reset_rate_limit_state,
    validate_jwt_secret,
    verify_client_credentials,
)


class TestSecurityJWTAuth(unittest.TestCase):
    def setUp(self):
        reset_rate_limit_state()

    def tearDown(self):
        reset_rate_limit_state()

    def test_validate_jwt_secret_valid(self):
        valid_secret = "9f8e4d2a1b7c6e5f3a0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f"
        self.assertEqual(validate_jwt_secret(valid_secret), valid_secret)

    def test_validate_jwt_secret_fatal_crash_on_weak(self):
        weak_secrets = [
            None,
            "",
            "   ",
            "short_key_123",
            "this_key_under_32_characters!",
            "secret123456789012345678901234567890",
            "super_changeme_token_key_1234567890!",
            "this_is_a_test_key_for_development_32ch",
            "password_protection_key_at_least_32_chars",
            "aaa-engine-secret-key-change-in-production",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        ]
        for weak in weak_secrets:
            with self.subTest(weak_secret=weak):
                with self.assertRaises(RuntimeError) as ctx:
                    validate_jwt_secret(weak)
                self.assertIn("FATAL SECURITY FAILURE", str(ctx.exception))

    def test_verify_client_credentials(self):
        self.assertTrue(
            verify_client_credentials(
                client_id="banking-shield-core",
                client_secret="banking-shield-super-secure-production-secret-2026",
                tenant_id="bank-alpha-001",
            )
        )
        self.assertFalse(
            verify_client_credentials(
                client_id="banking-shield-core",
                client_secret="wrong-secret",
                tenant_id="bank-alpha-001",
            )
        )

    def test_token_exchange_success(self):
        req = TokenRequest(
            client_id="banking-shield-core",
            client_secret="banking-shield-super-secure-production-secret-2026",
            tenant_id="bank-alpha-001",
        )
        response = exchange_token(req)
        self.assertIsNotNone(response.access_token)
        self.assertEqual(response.token_type, "bearer")
        self.assertEqual(response.expires_in, 900)
        token = response.access_token
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE)
        self.assertEqual(claims["tenant_id"], "bank-alpha-001")
        self.assertEqual(claims["client_id"], "banking-shield-core")

    def test_token_exchange_invalid_credentials(self):
        req = TokenRequest(
            client_id="banking-shield-core",
            client_secret="invalid-password",
            tenant_id="bank-alpha-001",
        )
        with self.assertRaises(HTTPException) as ctx:
            exchange_token(req)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_get_current_tenant_dependency(self):
        token = create_tenant_token(tenant_id="tenant-acme-corp", client_id="test-client-id")
        resolved = get_current_tenant(token=token)
        self.assertEqual(resolved, "tenant-acme-corp")
        with self.assertRaises(HTTPException):
            get_current_tenant(token=None)

    def test_rate_limiting_generic_error(self):
        tenant = "bank-alpha-001"
        user_ref = "usr-12345"
        for _ in range(60):
            enforce_rate_limit(tenant_id=tenant, user_ref=user_ref)
        with self.assertRaises(HTTPException) as ctx:
            enforce_rate_limit(tenant_id=tenant, user_ref=user_ref)
        self.assertEqual(ctx.exception.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(ctx.exception.detail, "RATE_LIMITED")

    def test_lockout_policy_generic_error(self):
        tenant = "bank-alpha-001"
        user_ref = "usr-victim"
        for _ in range(5):
            record_auth_failure(tenant_id=tenant, identifier=user_ref)
        with self.assertRaises(HTTPException) as ctx:
            enforce_lockout_policy(tenant_id=tenant, user_ref=user_ref)
        self.assertEqual(ctx.exception.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ctx.exception.detail, "LOCKED")

    def test_cors_wildcard_ban(self):
        test_app = FastAPI()
        orig_env = os.environ.get("ALLOWED_ORIGINS")
        try:
            os.environ["ALLOWED_ORIGINS"] = "https://bank.com,*,https://app.io"
            configure_cors(test_app)
            from fastapi.middleware.cors import CORSMiddleware

            cors_mw = next(m for m in test_app.user_middleware if m.cls == CORSMiddleware)
            origins = (
                cors_mw.kwargs.get("allow_origins")
                if hasattr(cors_mw, "kwargs")
                else cors_mw.options.get("allow_origins")
            )
            self.assertEqual(origins, [])
        finally:
            if orig_env is not None:
                os.environ["ALLOWED_ORIGINS"] = orig_env

    def test_cors_strict_allow(self):
        test_app = FastAPI()
        orig_env = os.environ.get("ALLOWED_ORIGINS")
        try:
            os.environ["ALLOWED_ORIGINS"] = "https://bank.com, https://app.io"
            configure_cors(test_app)
            from fastapi.middleware.cors import CORSMiddleware

            cors_mw = next(m for m in test_app.user_middleware if m.cls == CORSMiddleware)
            origins = (
                cors_mw.kwargs.get("allow_origins")
                if hasattr(cors_mw, "kwargs")
                else cors_mw.options.get("allow_origins")
            )
            self.assertEqual(origins, ["https://bank.com", "https://app.io"])
        finally:
            if orig_env is not None:
                os.environ["ALLOWED_ORIGINS"] = orig_env


if __name__ == "__main__":
    unittest.main()
