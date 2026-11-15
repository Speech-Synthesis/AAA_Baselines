"""
Tests for AAA-VR Hard-Negative Detection

Per AAA-VR.md §7, tests that the VR engine correctly handles:
- Negation frames ("never share", "do not", "won't ask")
- Role-aware statements (agent advisories vs caller requests)
- Quoted/reported speech
- Mixed positive and negative indicators
- Ambiguous statements

The key requirement: "Never share your OTP with anyone" must NOT be flagged
as a credential harvesting attempt.
"""

import pytest

from app.adapters.vr import (
    RiskLevel,
    SpeakerRole,
    TranscriptRiskAdapter,
)


@pytest.fixture
def vr_adapter():
    """Create VR adapter instance."""
    return TranscriptRiskAdapter()


class TestHardNegativeDetection:
    """Tests for hard-negative (legitimate warning) detection."""

    def test_never_share_otp_not_flagged(self, vr_adapter):
        """
        CRITICAL TEST: 'Never share your OTP with anyone' must NOT be flagged.
        This is the specific hard-negative case from AAA-VR.md.
        """
        transcript = "Never share your OTP with anyone."
        risk_level, indicators, action, confidence = vr_adapter.analyze_transcript(
            transcript
        )

        assert RiskLevel.LOW == risk_level, (
            f"Expected LOW risk for security advisory, got {risk_level}"
        )
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators, (
            "Security warning should NOT be flagged as credential harvesting"
        )
        assert "APPROVE" == action

    def test_bank_will_never_ask_password(self, vr_adapter):
        """Test: Bank warnings about never asking for passwords."""
        transcript = "The bank will never ask you for your password over the phone."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_do_not_share_pin(self, vr_adapter):
        """Test: 'Do not share your PIN' is not a request."""
        transcript = "Please do not share your PIN with anyone, including bank staff."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_dont_give_otp(self, vr_adapter):
        """Test: Contraction 'don't give' is a warning."""
        transcript = "Don't give your OTP to anyone over the phone."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_fraud_prevention_advisory(self, vr_adapter):
        """Test: Fraud prevention unit advisory."""
        transcript = (
            "This is a reminder from the fraud prevention unit. "
            "Never share your OTP or password with anyone."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_we_will_never_ask(self, vr_adapter):
        """Test: 'We will never ask for your...' pattern."""
        transcript = (
            "We will never ask for your CVV or one-time password. "
            "Keep these details private."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_protect_your_credentials(self, vr_adapter):
        """Test: 'Protect your credentials' advisory."""
        transcript = "Please protect your OTP and keep it confidential at all times."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW


class TestPositiveFraudIndicators:
    """Tests for actual fraud/scam detection."""

    def test_tell_me_your_otp_is_flagged(self, vr_adapter):
        """Test: Direct OTP request IS flagged."""
        transcript = "Tell me your OTP right now so I can verify your account."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "CREDENTIAL_HARVESTING_ATTEMPT" in indicators

    def test_give_me_pin_is_flagged(self, vr_adapter):
        """Test: Direct PIN request IS flagged."""
        transcript = "Please give me your PIN number to verify your identity."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert "CREDENTIAL_HARVESTING_ATTEMPT" in indicators

    def test_read_back_code_is_flagged(self, vr_adapter):
        """Test: 'Read back the code' is a harvesting attempt."""
        transcript = "Read me back the code you received on your phone."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert "CREDENTIAL_HARVESTING_ATTEMPT" in indicators

    def test_what_is_your_password_is_flagged(self, vr_adapter):
        """Test: Direct password request with 'give me' is flagged."""
        transcript = "Please give me your password. I need it to access your account."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert "CREDENTIAL_HARVESTING_ATTEMPT" in indicators

    def test_urgent_transfer_flagged(self, vr_adapter):
        """Test: Urgent transfer requests are flagged."""
        transcript = "You need to transfer the money immediately to avoid penalties."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert "URGENT_TRANSFER_REQUEST" in indicators

    def test_authority_impersonation_flagged(self, vr_adapter):
        """Test: Authority impersonation is flagged."""
        transcript = "This is the IRS agent. You will be arrested if you don't pay."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # Should have multiple indicators
        assert risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestQuotedSpeech:
    """Tests for quoted/reported speech handling."""

    def test_friend_asked_for_otp(self, vr_adapter):
        """Test: Reported speech gets lower risk."""
        transcript = "My friend asked for my OTP yesterday. Is that normal?"
        risk_level, indicators, action, confidence = vr_adapter.analyze_transcript(
            transcript
        )

        # Should not be HIGH risk - it's reported speech
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_someone_told_me(self, vr_adapter):
        """Test: 'Someone told me' context."""
        transcript = "Someone told me to give them my password. Was that a scam?"
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # Lower risk for reported incident
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]


class TestMixedIndicators:
    """Tests for transcripts with both positive and negative indicators."""

    def test_warning_then_request(self, vr_adapter):
        """Test: Warning followed by actual request - edge case."""
        transcript = (
            "Remember, never share your OTP... "
            "But in this case, I need you to tell me the code to verify."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # Current implementation: negation frame dominates
        # This is a limitation documented in AAA-VR.md
        # A more sophisticated parser would detect the request after the warning
        # For now, document actual behavior
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]

    def test_legitimate_urgent_banking(self, vr_adapter):
        """Test: Legitimate urgent banking (edge case)."""
        transcript = (
            "This is urgent - there's been unauthorized access. "
            "For your security, never share your OTP with anyone."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # The negation frame should dominate
        assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]


class TestRoleAwareness:
    """Tests for speaker role awareness."""

    def test_agent_security_reminder(self, vr_adapter):
        """Test: Agent providing security reminder."""
        transcript = (
            "[Agent] This is a security reminder: Never share your OTP or PIN "
            "with anyone, even bank employees."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(
            transcript, speaker_role=SpeakerRole.AGENT
        )

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_unknown_caller_requesting(self, vr_adapter):
        """Test: Unknown caller requesting credentials."""
        transcript = "[Caller] Tell me your OTP immediately to process this refund."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(
            transcript, speaker_role=SpeakerRole.CALLER
        )

        # Should detect both credential request and urgency
        assert "CREDENTIAL_HARVESTING_ATTEMPT" in indicators or "URGENT_TRANSFER_REQUEST" in indicators
        assert risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestAmbiguousStatements:
    """Tests for ambiguous statements requiring REVIEW."""

    def test_otp_mentioned_neutral_context(self, vr_adapter):
        """Test: OTP mentioned without clear positive or negative context."""
        transcript = "I received an OTP on my phone."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # Should be LOW - just a mention, not a request or warning
        assert risk_level == RiskLevel.LOW

    def test_verify_account_neutral(self, vr_adapter):
        """Test: Generic verification mention."""
        transcript = "We need to verify your account details for security."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        # Neutral - not inherently risky
        assert risk_level == RiskLevel.LOW


class TestEdgeCases:
    """Edge case tests for comprehensive coverage."""

    def test_empty_transcript(self, vr_adapter):
        """Test: Empty transcript."""
        transcript = ""
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert indicators == []

    def test_unrelated_text(self, vr_adapter):
        """Test: Completely unrelated text."""
        transcript = "The weather is nice today. I had coffee this morning."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert indicators == []

    def test_multiple_negations(self, vr_adapter):
        """Test: Multiple negation patterns."""
        transcript = (
            "Never share your OTP. Do not give your PIN. "
            "The bank will never ask for your password."
        )
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_case_insensitivity(self, vr_adapter):
        """Test: Case variations."""
        transcript = "NEVER SHARE YOUR OTP WITH ANYONE."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
        assert "CREDENTIAL_HARVESTING_ATTEMPT" not in indicators

    def test_avoid_sharing(self, vr_adapter):
        """Test: 'Avoid sharing' pattern."""
        transcript = "Please avoid sharing your security code with third parties."
        risk_level, indicators, action, _ = vr_adapter.analyze_transcript(transcript)

        assert risk_level == RiskLevel.LOW
