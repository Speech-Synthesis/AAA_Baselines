"""
Unit Tests for Host App Authentication & Banking Shield Decision Gateway
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

import time
import unittest
import uuid
from jose import jwt
from app.schemas.common import Decision
from app.security.host_auth import (
    HostAppAuthenticator,
    BankingShieldPolicy,
    evaluate_banking_decision,
)

class TestHostAuthBanking(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret-key-32-characters-minimum!!"
        self.authenticator = HostAppAuthenticator(self.secret)

    def test_evaluate_banking_decision_approve(self):
        decision, step_up = evaluate_banking_decision(
            similarity_score=0.90,
            is_spoof=False,
            policy_tier=BankingShieldPolicy.HIGH_VALUE,
        )
        self.assertEqual(decision, Decision.APPROVE)
        self.assertFalse(step_up)

    def test_evaluate_banking_decision_spoof_denied(self):
        decision, step_up = evaluate_banking_decision(
            similarity_score=0.99,
            is_spoof=True,
            policy_tier=BankingShieldPolicy.STANDARD,
        )
        self.assertEqual(decision, Decision.DENY)
        self.assertFalse(step_up)

    def test_evaluate_banking_decision_marginal_step_up(self):
        decision, step_up = evaluate_banking_decision(
            similarity_score=0.70,
            is_spoof=False,
            policy_tier=BankingShieldPolicy.HIGH_VALUE,
        )
        self.assertEqual(decision, Decision.STEP_UP)
        self.assertTrue(step_up)

    def test_validate_host_token_valid(self):
        token = jwt.encode(
            {"sub": "bank-shield-01", "aud": "aaa-engine", "exp": int(time.time()) + 60},
            self.secret,
            algorithm="HS256"
        )
        claims = self.authenticator.validate_host_token(token)
        self.assertEqual(claims["sub"], "bank-shield-01")

if __name__ == "__main__":
    unittest.main()
