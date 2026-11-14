"""
Unit Tests for Challenge Lifecycle State Machine and Tokens
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

import time
import unittest

from app.security.challenge_lifecycle import (
    ChallengeLifecycleError,
    ChallengeState,
    can_transition,
    generate_challenge_token,
    issue_capture_grant,
    validate_and_consume_challenge,
    verify_capture_grant,
)


class TestChallengeLifecycle(unittest.TestCase):
    def setUp(self):
        self.secret = b"test-challenge-signing-secret-key-32ch!"
        self.jwt_secret = "test-jwt-secret-key-for-capture-grant-32ch!"

    def test_state_machine_transitions(self):
        self.assertTrue(can_transition(ChallengeState.CREATED, ChallengeState.AUTHORIZED))
        self.assertTrue(can_transition(ChallengeState.AUTHORIZED, ChallengeState.CAPTURE_RECEIVED))
        self.assertTrue(can_transition(ChallengeState.CAPTURE_RECEIVED, ChallengeState.CONSUMED))
        self.assertTrue(can_transition(ChallengeState.CONSUMED, ChallengeState.COMPLETED))
        self.assertFalse(can_transition(ChallengeState.COMPLETED, ChallengeState.CREATED))
        self.assertFalse(can_transition(ChallengeState.CONSUMED, ChallengeState.AUTHORIZED))

    def test_generate_and_consume_token_success(self):
        token, exp_ts = generate_challenge_token(
            "user-01", "blue falcon seven", self.secret, ttl_seconds=90
        )
        self.assertEqual(len(token.split(".")), 3)

        new_state, meta = validate_and_consume_challenge(
            token=token,
            stored_user_id="user-01",
            stored_phrase="blue falcon seven",
            current_state=ChallengeState.CAPTURE_RECEIVED,
            expires_at_ts=exp_ts,
            secret_key=self.secret,
        )
        self.assertEqual(new_state, ChallengeState.CONSUMED)
        self.assertEqual(meta["user_id"], "user-01")

    def test_replay_attack_prevention(self):
        token, exp_ts = generate_challenge_token(
            "user-01", "blue falcon seven", self.secret, ttl_seconds=90
        )
        with self.assertRaises(ChallengeLifecycleError) as ctx:
            validate_and_consume_challenge(
                token=token,
                stored_user_id="user-01",
                stored_phrase="blue falcon seven",
                current_state=ChallengeState.CONSUMED,
                expires_at_ts=exp_ts,
                secret_key=self.secret,
            )
        self.assertIn("TOKEN_ALREADY_USED", str(ctx.exception))

    def test_tampered_signature_rejection(self):
        token, exp_ts = generate_challenge_token(
            "user-01", "blue falcon seven", self.secret, ttl_seconds=90
        )
        tampered_token = token[:-4] + "dead"
        with self.assertRaises(ChallengeLifecycleError) as ctx:
            validate_and_consume_challenge(
                token=tampered_token,
                stored_user_id="user-01",
                stored_phrase="blue falcon seven",
                current_state=ChallengeState.CAPTURE_RECEIVED,
                expires_at_ts=exp_ts,
                secret_key=self.secret,
            )
        self.assertIn("INVALID_TOKEN_SIGNATURE", str(ctx.exception))

    def test_capture_grant_lifecycle(self):
        exp_ts = int(time.time()) + 90
        grant = issue_capture_grant("chal-123", "tenant-alpha", exp_ts, self.jwt_secret)
        claims = verify_capture_grant(grant, "chal-123", self.jwt_secret)
        self.assertEqual(claims["sub"], "chal-123")
        self.assertEqual(claims["tenant_id"], "tenant-alpha")

        with self.assertRaises(ChallengeLifecycleError):
            verify_capture_grant(grant, "wrong-chal-id", self.jwt_secret)


if __name__ == "__main__":
    unittest.main()
