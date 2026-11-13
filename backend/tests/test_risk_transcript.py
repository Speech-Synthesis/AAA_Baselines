"""
Unit Tests for AAA-VR Risk Transcript Endpoint and Reason Codes
Author: Karthik Mallareddy (mrkarthik1811@gmail.com)
"""

import unittest
from app.schemas.risk import (
    RiskLevel,
    RiskAction,
    RiskIndicator,
    TranscriptRiskRequest,
)
from app.adapters.vr import TranscriptRiskAdapter
from app.api.v1.risk import evaluate_transcript_risk

class TestAAAVRRiskAnalysis(unittest.TestCase):
    def setUp(self):
        self.adapter = TranscriptRiskAdapter()

    def test_benign_transcript_low_risk(self):
        req = TranscriptRiskRequest(
            session_id="call-001",
            transcript="Hello, I would like to check my checking account balance please.",
        )
        res = self.adapter.predict(req, request_id="req-101")
        self.assertEqual(res.risk_level, RiskLevel.LOW)
        self.assertEqual(res.recommended_action, RiskAction.APPROVE.value)
        self.assertEqual(res.risk_indicators, [])

    def test_vishing_urgent_wire_high_risk(self):
        req = TranscriptRiskRequest(
            session_id="call-002",
            transcript="You must urgently transfer the funds immediately to this new account or the police will arrive.",
        )
        res = self.adapter.predict(req, request_id="req-102")
        self.assertIn(res.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])
        self.assertIn(RiskIndicator.URGENT_TRANSFER_REQUEST.value, res.risk_indicators)
        self.assertIn(RiskIndicator.PRESSURE_TACTICS_DETECTED.value, res.risk_indicators)
        self.assertIn(res.recommended_action, [RiskAction.STEP_UP.value, RiskAction.DENY.value])

    def test_credential_harvesting_critical(self):
        req = TranscriptRiskRequest(
            session_id="call-003",
            transcript="I am from the fraud department. Provide your otp, pin number, and password right now or face arrest.",
        )
        res = self.adapter.predict(req, request_id="req-103")
        self.assertEqual(res.risk_level, RiskLevel.CRITICAL)
        self.assertEqual(res.recommended_action, RiskAction.DENY.value)
        self.assertIn(RiskIndicator.CREDENTIAL_HARVESTING_ATTEMPT.value, res.risk_indicators)
        self.assertIn(RiskIndicator.IMPERSONATION_ATTEMPT.value, res.risk_indicators)

    def test_direct_endpoint_handler(self):
        req = TranscriptRiskRequest(
            session_id="call-004",
            transcript="Please transfer to account ending in 4567 immediately.",
        )
        res = evaluate_transcript_risk(
            request=req,
            tenant_id="bank-alpha-001",
            x_request_id="custom-req-id-777",
            _=None,
        )
        self.assertEqual(res.request_id, "custom-req-id-777")
        self.assertEqual(res.session_id, "call-004")
        self.assertIn(res.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])

if __name__ == "__main__":
    unittest.main()
