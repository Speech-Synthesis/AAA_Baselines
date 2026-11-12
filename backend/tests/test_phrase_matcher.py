"""
AAA-ASR Phrase Matcher — Comprehensive Test Suite

Tests the deterministic exact-match phrase verification logic as specified
in 02_MODEL_ARCHITECTURE/AAA-ASR.md Section 7.

Target: >= 100 test cases covering all required categories.
Uses pytest parametrization for comprehensive coverage.

Categories covered:
1-5: Exact match, case normalization (lower/upper/mixed), punctuation, whitespace
6-10: Multiple spaces, newlines/tabs, approved fillers, digit-to-word
11-15: Missing words, extra words, repeated words, reordered words, incorrect numbers
16-20: Empty transcript, empty expected, whitespace-only, no-speech, low-confidence
21-25: Too-short audio, expired challenge, invalid inputs, homophones, punctuation-only
26-30: Repeated punctuation, normalization collisions, Unicode/apostrophe, 
       regression against old fuzzy matching, near-miss rejection

Run with:
    python -m pytest backend/tests/test_phrase_matcher.py -v
"""

import sys
import os
import pytest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.aaa_asr.phrase_matcher import (
    PhraseVerifier,
    PhraseResult,
    normalize_text,
    verify_phrase,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def verifier():
    """Create a PhraseVerifier with default settings."""
    return PhraseVerifier(confidence_threshold=0.5)


# ---------------------------------------------------------------------------
# Category 1: Exact phrase match
# ---------------------------------------------------------------------------

class TestExactMatch:
    """Test exact phrase matches that should produce OK."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("Seven Red Chair Twenty", "seven red chair twenty"),
        ("blue green yellow", "blue green yellow"),
        ("one two three four five", "one two three four five"),
        ("cat dog fish bird", "cat dog fish bird"),
        ("open close start stop", "open close start stop"),
    ])
    def test_exact_phrase_match(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True

    def test_identical_case(self):
        result = verify_phrase(expected="hello world", transcript="hello world")
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 2-4: Case normalization (lowercase, uppercase, mixed)
# ---------------------------------------------------------------------------

class TestCaseNormalization:
    """Test that case differences are normalized correctly."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("Seven Red Chair Twenty", "SEVEN RED CHAIR TWENTY"),
        ("HELLO WORLD", "hello world"),
        ("HeLLo WoRLd", "hello world"),
        ("Seven Red Chair Twenty", "sEvEn ReD cHaIr TwEnTy"),
        ("BLUE GREEN", "blue green"),
        ("Alpha Bravo Charlie", "alpha bravo charlie"),
        ("Alpha Bravo Charlie", "ALPHA BRAVO CHARLIE"),
    ])
    def test_case_insensitive_match(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 5: Punctuation handling
# ---------------------------------------------------------------------------

class TestPunctuation:
    """Test that punctuation is stripped correctly."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("hello, world!", "hello world"),
        ("hello world", "hello, world!"),
        ("seven. red. chair.", "seven red chair"),
        ("test phrase!", "test phrase"),
        ("what? is? this?", "what is this"),
    ])
    def test_punctuation_stripped(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 6-9: Whitespace handling (leading, trailing, multiple, newlines/tabs)
# ---------------------------------------------------------------------------

class TestWhitespace:
    """Test whitespace normalization."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("  seven red chair twenty  ", "seven red chair twenty"),
        ("seven red chair twenty", "  seven red chair twenty  "),
        ("seven  red  chair  twenty", "seven red chair twenty"),
        ("seven   red    chair     twenty", "seven red chair twenty"),
        ("seven\tred\tchair\ttwenty", "seven red chair twenty"),
        ("seven\nred\nchair\ntwenty", "seven red chair twenty"),
        ("seven \r\n red \r\n chair", "seven red chair"),
        ("\t  seven  \t  red  \t", "seven red"),
    ])
    def test_whitespace_normalized(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 10: Approved filler words
# ---------------------------------------------------------------------------

class TestFillerWords:
    """Test that approved filler words are removed."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "um seven red chair twenty"),
        ("seven red chair twenty", "seven uh red chair twenty"),
        ("seven red chair twenty", "seven red er chair twenty"),
        ("seven red chair twenty", "seven red chair hmm twenty"),
        ("seven red chair twenty", "um uh seven red er chair hmm twenty"),
        ("seven red chair twenty", "seven red chair twenty erm"),
        ("seven red chair twenty", "ah seven red chair twenty"),
    ])
    def test_filler_words_removed(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 11: Digit-to-word conversion
# ---------------------------------------------------------------------------

class TestDigitConversion:
    """Test digit <-> word normalization."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "7 red chair 20"),
        ("7 red chair 20", "seven red chair twenty"),
        ("1 2 3", "one two three"),
        ("zero five nine", "0 5 9"),
        ("four eight", "4 8"),
        ("ten eleven twelve", "10 11 12"),
    ])
    def test_digit_word_conversion(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 12: Missing words — must REJECT
# ---------------------------------------------------------------------------

class TestMissingWords:
    """Test that missing words cause MISMATCH."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "seven red chair"),
        ("seven red chair twenty", "seven red twenty"),
        ("seven red chair twenty", "red chair twenty"),
        ("seven red chair twenty", "seven"),
        ("seven red chair twenty", "seven red"),
        ("one two three four five", "one two three four"),
        ("alpha bravo charlie", "alpha bravo"),
        ("open close start stop", "open close start"),
    ])
    def test_missing_words_rejected(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 13: Extra words — must REJECT
# ---------------------------------------------------------------------------

class TestExtraWords:
    """Test that extra words cause MISMATCH."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "seven red chair twenty five"),
        ("seven red chair twenty", "please seven red chair twenty"),
        ("seven red chair twenty", "seven extra red chair twenty"),
        ("hello world", "hello beautiful world"),
        ("one two three", "one two three four"),
        ("blue green", "blue green yellow"),
    ])
    def test_extra_words_rejected(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 14: Repeated words — must REJECT
# ---------------------------------------------------------------------------

class TestRepeatedWords:
    """Test that repeated words cause MISMATCH (not collapsed)."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "seven seven red chair twenty"),
        ("seven red chair twenty", "seven red red chair twenty"),
        ("seven red chair twenty", "seven red chair twenty twenty"),
        ("hello world", "hello hello world"),
        ("one two three", "one one two three"),
        ("blue green", "blue blue green green"),
    ])
    def test_repeated_words_rejected(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 15: Reordered words — must REJECT
# ---------------------------------------------------------------------------

class TestReorderedWords:
    """Test that reordered words cause MISMATCH."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("seven red chair twenty", "twenty chair red seven"),
        ("seven red chair twenty", "red seven chair twenty"),
        ("seven red chair twenty", "seven chair red twenty"),
        ("one two three", "three two one"),
        ("alpha bravo charlie", "charlie bravo alpha"),
        ("open close start", "start close open"),
    ])
    def test_reordered_words_rejected(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 16: Incorrect numbers — must REJECT
# ---------------------------------------------------------------------------

class TestIncorrectNumbers:
    """Test that incorrect numbers cause MISMATCH."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("Seven Red Chair Twenty", "Seven Red Chair Thirty"),
        ("seven red chair twenty", "seven red chair nineteen"),
        ("one two three", "one two four"),
        ("five six seven", "five six eight"),
        ("zero one two", "zero one three"),
        ("ten twenty thirty", "ten twenty forty"),
    ])
    def test_incorrect_numbers_rejected(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 17: Empty transcript — must return NO_SPEECH
# ---------------------------------------------------------------------------

class TestEmptyTranscript:
    """Test handling of empty or missing transcripts."""
    
    def test_empty_string_transcript(self):
        result = verify_phrase(expected="seven red chair twenty", transcript="")
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_whitespace_only_transcript(self):
        result = verify_phrase(expected="seven red chair twenty", transcript="   ")
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_tabs_only_transcript(self):
        result = verify_phrase(expected="seven red chair twenty", transcript="\t\t")
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_newlines_only_transcript(self):
        result = verify_phrase(expected="seven red chair twenty", transcript="\n\n")
        assert result.code == "NO_SPEECH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 18: Empty expected phrase
# ---------------------------------------------------------------------------

class TestEmptyExpected:
    """Test handling of empty expected phrases."""
    
    def test_empty_expected(self):
        result = verify_phrase(expected="", transcript="seven red chair twenty")
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_whitespace_expected(self):
        result = verify_phrase(expected="   ", transcript="seven red chair twenty")
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 19: No-speech condition
# ---------------------------------------------------------------------------

class TestNoSpeech:
    """Test no-speech probability handling."""
    
    def test_high_no_speech_prob(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            no_speech_prob=0.95,
        )
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_low_no_speech_prob_allows_match(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            no_speech_prob=0.1,
        )
        assert result.code == "OK"
        assert result.match is True

    def test_borderline_no_speech_prob(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            no_speech_prob=0.8,
        )
        # 0.8 is at the threshold, not above it
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 20: Low-confidence condition
# ---------------------------------------------------------------------------

class TestLowConfidence:
    """Test confidence threshold enforcement."""
    
    def test_low_confidence_rejected(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=0.1,
        )
        assert result.code == "LOW_CONF"
        assert result.match is False

    def test_high_confidence_accepted(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=0.9,
        )
        assert result.code == "OK"
        assert result.match is True

    def test_confidence_does_not_fix_mismatch(self):
        """High confidence must NOT turn a mismatch into OK."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair thirty",
            confidence=0.99,
        )
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_none_confidence_accepted(self):
        """When confidence is None, no confidence check is applied."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=None,
        )
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 21: Too-short audio condition
# ---------------------------------------------------------------------------

class TestTooShort:
    """Test audio duration minimum enforcement (1.0s min per SHARED.md)."""
    
    def test_too_short_audio(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            audio_duration=0.1,
        )
        assert result.code == "TOO_SHORT"
        assert result.match is False

    def test_boundary_sub_1s_rejected(self):
        """0.9s is below 1.0s minimum -> TOO_SHORT."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            audio_duration=0.9,
        )
        assert result.code == "TOO_SHORT"
        assert result.match is False

    def test_boundary_1s_accepted(self):
        """1.0s meets minimum -> OK."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            audio_duration=1.0,
        )
        assert result.code == "OK"
        assert result.match is True

    def test_adequate_audio_duration(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            audio_duration=3.0,
        )
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 22: Expired challenge
# ---------------------------------------------------------------------------

class TestExpiredChallenge:
    """Test expired challenge handling."""
    
    def test_expired_challenge_rejected(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            challenge_expired=True,
        )
        assert result.code == "EXPIRED_CHALLENGE"
        assert result.match is False

    def test_expired_with_perfect_match_still_rejected(self):
        """Even a perfect match with high confidence must be rejected if expired."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=1.0,
            challenge_expired=True,
        )
        assert result.code == "EXPIRED_CHALLENGE"
        assert result.match is False

    def test_timeout_rejected(self):
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            challenge_timed_out=True,
        )
        assert result.code == "TIMEOUT"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 23: Invalid input types
# ---------------------------------------------------------------------------

class TestInvalidInputs:
    """Test handling of invalid input types."""
    
    def test_none_transcript(self):
        result = verify_phrase(expected="hello world", transcript=None)
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_none_expected(self):
        result = verify_phrase(expected=None, transcript="hello world")
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_integer_transcript(self):
        result = verify_phrase(expected="hello world", transcript=123)
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_integer_expected(self):
        result = verify_phrase(expected=123, transcript="hello world")
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 24: Homophone/minimal-pair edge cases
# ---------------------------------------------------------------------------

class TestHomophones:
    """Test homophone and minimal-pair handling from curated vocabulary."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("red", "read"),         # Different words
        ("four", "for"),         # Homophone but different spelling
        ("eight", "ate"),        # Number homophone
        ("two", "too"),          # Number homophone
        ("one", "won"),          # Number homophone
        ("blue", "blew"),        # Color homophone
    ])
    def test_homophones_rejected_as_mismatch(self, expected, transcript):
        """Homophones that are different words should be rejected."""
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 25: Punctuation-only input
# ---------------------------------------------------------------------------

class TestPunctuationOnly:
    """Test handling of punctuation-only inputs."""
    
    def test_punctuation_only_transcript(self):
        result = verify_phrase(expected="hello world", transcript="...")
        assert result.code == "NO_SPEECH"
        assert result.match is False

    def test_punctuation_only_expected(self):
        result = verify_phrase(expected="...", transcript="hello world")
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_symbols_only_transcript(self):
        result = verify_phrase(expected="hello world", transcript="!@#$%")
        assert result.code == "NO_SPEECH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 26: Repeated punctuation
# ---------------------------------------------------------------------------

class TestRepeatedPunctuation:
    """Test handling of repeated punctuation around words."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("hello world", "hello... world..."),
        ("hello world", "hello!!! world!!!"),
        ("seven red", "seven,,,, red...."),
    ])
    def test_repeated_punctuation_normalized(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Category 27: Normalization collisions
# ---------------------------------------------------------------------------

class TestNormalizationCollisions:
    """Test that normalization doesn't cause false matches."""
    
    def test_oh_becomes_zero(self):
        """'oh' is aliased to 'zero' for digit context."""
        result = verify_phrase(expected="zero", transcript="oh")
        assert result.code == "OK"
        assert result.match is True

    def test_oh_vs_one(self):
        result = verify_phrase(expected="one", transcript="oh")
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_different_digit_words(self):
        result = verify_phrase(expected="seven", transcript="eleven")
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 28: Unicode and apostrophe edge cases
# ---------------------------------------------------------------------------

class TestUnicode:
    """Test Unicode normalization and apostrophe handling."""
    
    def test_curly_apostrophe(self):
        """Curly apostrophes should be normalized via NFKC."""
        result = verify_phrase(expected="don't stop", transcript="don't stop")
        # Both should normalize identically
        assert result.code == "OK"
        assert result.match is True

    def test_em_dash(self):
        result = verify_phrase(expected="hello world", transcript="hello—world")
        assert result.code == "OK"
        assert result.match is True

    def test_fullwidth_numbers(self):
        """Full-width digits should be normalized via NFKC."""
        result = verify_phrase(expected="seven", transcript="7")
        assert result.code == "OK"
        assert result.match is True

    def test_accented_characters(self):
        """Accented characters remain after normalization."""
        result = verify_phrase(expected="café", transcript="cafe")
        # 'é' -> 'e' only if NFKC handles it; they may differ
        # This tests that accents don't crash
        assert isinstance(result, PhraseResult)


# ---------------------------------------------------------------------------
# Category 29: Regression against old fuzzy matching
# ---------------------------------------------------------------------------

class TestFuzzyRejection:
    """
    Regression tests: phrases that the OLD fuzzy SequenceMatcher at
    threshold 0.6 would have accepted, but MUST now be rejected.
    """
    
    @pytest.mark.parametrize("expected,transcript", [
        # One word different (high similarity ~0.75+)
        ("seven red chair twenty", "seven red chair thirty"),
        ("seven red chair twenty", "seven red sofa twenty"),
        ("seven red chair twenty", "seven blue chair twenty"),
        
        # Very similar but not identical
        ("open close start stop", "open close start shop"),
        ("blue green yellow red", "blue green yellow bed"),
        
        # Missing one word (still high similarity)
        ("seven red chair twenty", "seven red twenty"),
        ("alpha bravo charlie delta", "alpha bravo charlie"),
        
        # One extra word
        ("seven red chair", "seven red chair twenty"),
        ("hello world", "hello there world"),
        
        # Near-homophone substitution
        ("seven red chair twenty", "seven read chair twenty"),
    ])
    def test_near_miss_rejected(self, expected, transcript):
        """Near-miss phrases must be REJECTED even if similarity is high."""
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "MISMATCH"
        assert result.match is False


# ---------------------------------------------------------------------------
# Category 30: British/American spelling
# ---------------------------------------------------------------------------

class TestSpellingVariants:
    """Test British/American spelling normalization."""
    
    @pytest.mark.parametrize("expected,transcript", [
        ("color red blue", "colour red blue"),
        ("favorite green", "favourite green"),
        ("gray sky", "grey sky"),
        ("center point", "centre point"),
        ("analyze data", "analyse data"),
    ])
    def test_spelling_variants_match(self, expected, transcript):
        result = verify_phrase(expected=expected, transcript=transcript)
        assert result.code == "OK"
        assert result.match is True


# ---------------------------------------------------------------------------
# Normalization unit tests
# ---------------------------------------------------------------------------

class TestNormalization:
    """Direct tests of the normalize_text function."""
    
    def test_basic_lowercase(self):
        assert normalize_text("HELLO WORLD") == "hello world"

    def test_strip_punctuation(self):
        assert normalize_text("hello, world!") == "hello world"

    def test_collapse_whitespace(self):
        assert normalize_text("hello   world") == "hello world"

    def test_digit_to_word(self):
        assert normalize_text("7") == "seven"

    def test_multi_digit(self):
        assert normalize_text("20") == "twenty"

    def test_filler_removal(self):
        assert normalize_text("um hello uh world") == "hello world"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_none_input(self):
        assert normalize_text(None) == ""

    def test_pure_punctuation(self):
        assert normalize_text("...!!!") == ""

    def test_underscore_removal(self):
        assert normalize_text("hello_world") == "hello world"

    def test_contraction_expansion(self):
        assert normalize_text("don't") == "do not"

    def test_oh_alias(self):
        assert normalize_text("oh") == "zero"

    def test_tabs_and_newlines(self):
        assert normalize_text("hello\t\nworld") == "hello world"


# ---------------------------------------------------------------------------
# PhraseVerifier class tests
# ---------------------------------------------------------------------------

class TestPhraseVerifierClass:
    """Test the PhraseVerifier class directly."""
    
    def test_custom_confidence_threshold(self):
        verifier = PhraseVerifier(confidence_threshold=0.8)
        result = verifier.verify(
            expected="hello world",
            transcript="hello world",
            confidence=0.7,
        )
        assert result.code == "LOW_CONF"
        assert result.match is False

    def test_result_contains_normalized_forms(self):
        result = verify_phrase(
            expected="Seven Red Chair Twenty",
            transcript="seven red chair thirty",
        )
        assert result.normalized_expected == "seven red chair twenty"
        assert result.normalized_hyp == "seven red chair thirty"
        assert result.code == "MISMATCH"

    def test_result_contains_hypothesis(self):
        result = verify_phrase(
            expected="hello world",
            transcript="hello world",
        )
        assert result.hypothesis == "hello world"
        assert result.code == "OK"

    def test_fail_closed_on_missing_data(self):
        """Missing required data should fail closed."""
        result = verify_phrase(expected="hello", transcript="")
        assert result.match is False


# ---------------------------------------------------------------------------
# Security invariant tests
# ---------------------------------------------------------------------------

class TestSecurityInvariants:
    """Test critical security invariants."""
    
    def test_high_confidence_cannot_fix_mismatch(self):
        """SECURITY: High confidence must NEVER turn a mismatch into OK."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair thirty",
            confidence=1.0,
        )
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_expired_always_fails(self):
        """SECURITY: Expired challenge always fails regardless of match."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=1.0,
            challenge_expired=True,
        )
        assert result.code == "EXPIRED_CHALLENGE"
        assert result.match is False

    def test_exact_match_with_low_conf_fails(self):
        """SECURITY: Exact phrase with insufficient confidence must not be approved."""
        result = verify_phrase(
            expected="seven red chair twenty",
            transcript="seven red chair twenty",
            confidence=0.05,
        )
        assert result.code == "LOW_CONF"
        assert result.match is False

    def test_no_fuzzy_acceptance_path(self):
        """SECURITY: No fuzzy matching should exist. Near-misses rejected."""
        near_miss_pairs = [
            ("seven red chair twenty", "seven red chair twenty one"),
            ("seven red chair twenty", "seven red chairs twenty"),
            ("seven red chair twenty", "seven red chair"),
            ("seven red chair twenty", "sven red chair twenty"),
            ("seven red chair twenty", "seven rad chair twenty"),
        ]
        for expected, transcript in near_miss_pairs:
            result = verify_phrase(expected=expected, transcript=transcript)
            assert result.match is False, (
                f"Near-miss should be rejected: '{expected}' vs '{transcript}'"
            )

    def test_fail_closed_behavior(self):
        """SECURITY: Invalid inputs fail closed (never return OK)."""
        invalid_cases = [
            (None, None),
            ("", ""),
            ("   ", "   "),
            (None, "hello"),
            ("hello", None),
        ]
        for expected, transcript in invalid_cases:
            result = verify_phrase(expected=expected, transcript=transcript)
            assert result.match is False, (
                f"Invalid input should fail closed: expected={expected!r}, transcript={transcript!r}"
            )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Additional edge cases."""
    
    def test_single_word_match(self):
        result = verify_phrase(expected="seven", transcript="seven")
        assert result.code == "OK"
        assert result.match is True

    def test_single_word_mismatch(self):
        result = verify_phrase(expected="seven", transcript="eight")
        assert result.code == "MISMATCH"
        assert result.match is False

    def test_very_long_phrase(self):
        words = ["seven", "red", "chair", "twenty", "blue", "green"]
        phrase = " ".join(words)
        result = verify_phrase(expected=phrase, transcript=phrase)
        assert result.code == "OK"
        assert result.match is True

    def test_multiple_fillers_in_transcript(self):
        result = verify_phrase(
            expected="hello world",
            transcript="um uh er hmm hello erm world ah",
        )
        assert result.code == "OK"
        assert result.match is True

    def test_digit_and_word_mixed(self):
        result = verify_phrase(expected="7 red 20", transcript="seven red twenty")
        assert result.code == "OK"
        assert result.match is True

    def test_contraction_in_expected(self):
        """Contractions should be expanded identically."""
        result = verify_phrase(expected="I can't go", transcript="i cannot go")
        assert result.code == "OK"
        assert result.match is True

    def test_mixed_case_punctuation_whitespace(self):
        result = verify_phrase(
            expected="  Seven, Red!! Chair...  Twenty  ",
            transcript="seven red chair twenty",
        )
        assert result.code == "OK"
        assert result.match is True

    def test_all_conditions_combined_pass(self):
        """All conditions met — should pass."""
        result = verify_phrase(
            expected="Seven Red Chair Twenty",
            transcript="seven red chair twenty",
            confidence=0.9,
            audio_duration=3.0,
            no_speech_prob=0.05,
            challenge_expired=False,
            challenge_timed_out=False,
        )
        assert result.code == "OK"
        assert result.match is True

    def test_all_conditions_combined_fail_mismatch(self):
        """Good conditions but wrong phrase — should fail."""
        result = verify_phrase(
            expected="Seven Red Chair Twenty",
            transcript="seven red chair thirty",
            confidence=0.9,
            audio_duration=3.0,
            no_speech_prob=0.05,
        )
        assert result.code == "MISMATCH"
        assert result.match is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
