"""
AAA-ASR Phrase Matcher — Deterministic Exact-Match Challenge Phrase Verification

This module implements the approved AAA-ASR phrase verification logic as specified
in 02_MODEL_ARCHITECTURE/AAA-ASR.md Section 7.

Key design decisions:
- Exact match after safe normalization. No fuzzy acceptance.
- Confidence can only tighten acceptance; it cannot turn a text mismatch into a pass.
- Fail closed: any error or missing data results in rejection.
- One missing, extra, reordered, or different word is a MISMATCH.

Normalization pipeline (applied to both expected and recognized text identically):
1. Unicode NFKC + lowercase
2. Strip punctuation, hyphens, extra spaces
3. Remove approved fillers: um, uh, er, hmm
4. Numbers: digit <-> word conversion (limited to challenge vocabulary)
5. British/American spelling map for vocabulary entries
6. Do NOT collapse repeated words (a repeated word is a real error)

Result codes: OK, MISMATCH, LOW_CONF, NO_SPEECH, TOO_SHORT, TIMEOUT, EXPIRED_CHALLENGE
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import unicodedata


# ---------------------------------------------------------------------------
# Result Data Class
# ---------------------------------------------------------------------------

@dataclass
class PhraseResult:
    """Verification result from the phrase matcher.
    
    Attributes:
        code: One of OK, MISMATCH, LOW_CONF, NO_SPEECH, TOO_SHORT, TIMEOUT, EXPIRED_CHALLENGE
        match: Whether the phrase matched exactly after normalization
        hypothesis: Raw ASR transcript
        normalized_hyp: Normalized ASR transcript
        normalized_expected: Normalized expected phrase
        confidence: ASR confidence score (0.0 - 1.0), None if unavailable
        reason: Human-readable reason for the decision
    """
    code: str
    match: bool
    hypothesis: str = ""
    normalized_hyp: str = ""
    normalized_expected: str = ""
    confidence: Optional[float] = None
    reason: str = ""


# ---------------------------------------------------------------------------
# Constants — Challenge Vocabulary Configuration
# ---------------------------------------------------------------------------

# Approved filler words to strip from ASR transcripts
FILLER_WORDS = frozenset({"um", "uh", "er", "hmm", "erm", "ah"})

# Digit-to-word mapping (bidirectional normalization)
# We normalize WORDS to their WORD forms for consistent comparison.
# Both "7" and "seven" normalize to "seven".
DIGIT_TO_WORD = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "11": "eleven",
    "12": "twelve",
    "13": "thirteen",
    "14": "fourteen",
    "15": "fifteen",
    "16": "sixteen",
    "17": "seventeen",
    "18": "eighteen",
    "19": "nineteen",
    "20": "twenty",
    "21": "twenty one",
    "30": "thirty",
    "40": "forty",
    "50": "fifty",
    "60": "sixty",
    "70": "seventy",
    "80": "eighty",
    "90": "ninety",
}

# Also handle "oh" -> "zero" in digit context
WORD_ALIASES = {
    "oh": "zero",
}

# British/American spelling normalization (limited to challenge vocabulary)
SPELLING_MAP = {
    "colour": "color",
    "favourite": "favorite",
    "grey": "gray",
    "licence": "license",
    "defence": "defense",
    "catalogue": "catalog",
    "centre": "center",
    "metre": "meter",
    "litre": "liter",
    "analyse": "analyze",
    "organise": "organize",
    "recognise": "recognize",
    "realise": "realize",
    "apologise": "apologize",
}

# Contractions to expand consistently
CONTRACTIONS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "couldn't": "could not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "i'm": "i am",
    "you're": "you are",
    "we're": "we are",
    "they're": "they are",
    "he's": "he is",
    "she's": "she is",
    "it's": "it is",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "i'll": "i will",
    "you'll": "you will",
    "we'll": "we will",
    "they'll": "they will",
    "i'd": "i would",
    "you'd": "you would",
    "we'd": "we would",
    "they'd": "they would",
    "let's": "let us",
}


# ---------------------------------------------------------------------------
# Normalization Functions
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Apply the approved normalization pipeline to a text string.
    
    This function is deterministic and applies the SAME transformations
    to both expected challenge phrases and ASR transcripts.
    
    Pipeline:
    1. Unicode NFKC normalization + lowercase
    2. Expand contractions
    3. Strip punctuation and hyphens
    4. Normalize whitespace (collapse multiple spaces, strip leading/trailing)
    5. Remove approved filler words
    6. Convert digits to word form
    7. Apply spelling normalization
    8. Apply word aliases (e.g., "oh" -> "zero")
    
    Returns:
        Normalized text string
    """
    if not isinstance(text, str):
        return ""
    
    # Step 1: Unicode NFKC + lowercase
    text = unicodedata.normalize("NFKC", text).lower().strip()
    
    # Step 2: Expand contractions (before punctuation removal to catch apostrophes)
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(
            r'\b' + re.escape(contraction) + r'\b',
            expansion,
            text
        )
    
    # Step 3: Strip punctuation and hyphens (keep alphanumeric and spaces)
    text = re.sub(r"[^\w\s]", " ", text)
    # Also replace underscores
    text = text.replace("_", " ")
    
    # Step 4: Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Step 5: Remove approved filler words
    words = text.split()
    words = [w for w in words if w not in FILLER_WORDS]
    
    # Step 6: Convert digits to word form
    normalized_words = []
    for word in words:
        if word in DIGIT_TO_WORD:
            # Split multi-word expansions (e.g., "21" -> "twenty one")
            normalized_words.extend(DIGIT_TO_WORD[word].split())
        else:
            normalized_words.append(word)
    words = normalized_words
    
    # Step 7: Apply spelling normalization
    words = [SPELLING_MAP.get(w, w) for w in words]
    
    # Step 8: Apply word aliases
    words = [WORD_ALIASES.get(w, w) for w in words]
    
    return " ".join(words)


# ---------------------------------------------------------------------------
# Phrase Verifier
# ---------------------------------------------------------------------------

class PhraseVerifier:
    """
    Deterministic phrase verifier for AAA challenge-response authentication.
    
    The verifier receives:
    - Expected challenge phrase (from server-side challenge record)
    - ASR transcript (hypothesis from Whisper)
    - Confidence score from ASR
    - Challenge validity information (expired, timeout, etc.)
    
    It returns a PhraseResult with a deterministic verification decision.
    
    SECURITY INVARIANTS:
    - An incorrect phrase NEVER becomes accepted because of a high confidence score.
    - An exact phrase with insufficient confidence MUST NOT be approved.
    - An expired challenge MUST NEVER be accepted.
    - Fail closed on any error.
    """
    
    # Default confidence threshold
    DEFAULT_CONFIDENCE_THRESHOLD = 0.5
    
    # Minimum audio duration in seconds (aligned with SHARED.md Section 2: < 1.0s = TOO_SHORT)
    MIN_AUDIO_DURATION = 1.0
    
    def __init__(self, confidence_threshold: float = None):
        """
        Initialize the phrase verifier.
        
        Args:
            confidence_threshold: Minimum ASR confidence to accept. 
                                  Defaults to DEFAULT_CONFIDENCE_THRESHOLD.
        """
        self.confidence_threshold = (
            confidence_threshold 
            if confidence_threshold is not None 
            else self.DEFAULT_CONFIDENCE_THRESHOLD
        )
    
    def verify(
        self,
        expected: str,
        transcript: str,
        confidence: Optional[float] = None,
        audio_duration: Optional[float] = None,
        no_speech_prob: Optional[float] = None,
        challenge_expired: bool = False,
        challenge_timed_out: bool = False,
    ) -> PhraseResult:
        """
        Verify that a transcript matches the expected challenge phrase.
        
        This is the ONLY entry point for phrase verification in the
        authentication path. It uses exact matching after safe normalization.
        
        Args:
            expected: The expected challenge phrase (from server-side record)
            transcript: The ASR hypothesis text
            confidence: ASR confidence score (0.0-1.0), None if unavailable
            audio_duration: Duration of the audio in seconds, None if unknown
            no_speech_prob: Whisper's no-speech probability, None if unavailable
            challenge_expired: Whether the challenge has expired
            challenge_timed_out: Whether the challenge timed out
            
        Returns:
            PhraseResult with verification decision
        """
        # ------- Pre-checks (fail closed) -------
        
        # Check for expired challenge FIRST — never accept expired
        if challenge_expired:
            return PhraseResult(
                code="EXPIRED_CHALLENGE",
                match=False,
                reason="Challenge has expired. A new challenge is required.",
            )
        
        # Check for timeout
        if challenge_timed_out:
            return PhraseResult(
                code="TIMEOUT",
                match=False,
                reason="Challenge timed out. A new challenge is required.",
            )
        
        # Validate inputs
        if not isinstance(expected, str) or not expected.strip():
            return PhraseResult(
                code="MISMATCH",
                match=False,
                reason="Expected phrase is empty or invalid.",
            )
        
        if not isinstance(transcript, str) or not transcript.strip():
            return PhraseResult(
                code="NO_SPEECH",
                match=False,
                hypothesis=transcript if isinstance(transcript, str) else "",
                reason="No speech detected in the audio.",
            )
        
        # Check audio duration if provided
        if audio_duration is not None and audio_duration < self.MIN_AUDIO_DURATION:
            return PhraseResult(
                code="TOO_SHORT",
                match=False,
                hypothesis=transcript,
                reason=f"Audio too short ({audio_duration:.1f}s). Minimum {self.MIN_AUDIO_DURATION}s required.",
            )
        
        # Check no-speech probability if provided
        if no_speech_prob is not None and no_speech_prob > 0.8:
            return PhraseResult(
                code="NO_SPEECH",
                match=False,
                hypothesis=transcript,
                reason=f"High no-speech probability ({no_speech_prob:.2f}). No valid speech detected.",
            )
        
        # ------- Normalization -------
        normalized_expected = normalize_text(expected)
        normalized_hyp = normalize_text(transcript)
        
        # If transcript normalizes to empty (e.g. only punctuation, symbols, fillers),
        # no speech was recognized
        if not normalized_hyp:
            return PhraseResult(
                code="NO_SPEECH",
                match=False,
                hypothesis=transcript,
                normalized_hyp="",
                normalized_expected=normalized_expected,
                reason="No speech or words recognized in the transcript.",
            )
        
        # If expected normalizes to empty, invalid challenge phrase
        if not normalized_expected:
            return PhraseResult(
                code="MISMATCH",
                match=False,
                hypothesis=transcript,
                normalized_hyp=normalized_hyp,
                normalized_expected="",
                reason="Expected phrase is empty after normalization.",
            )

        # ------- Exact comparison -------
        is_exact_match = (normalized_expected == normalized_hyp)
        
        if not is_exact_match:
            return PhraseResult(
                code="MISMATCH",
                match=False,
                hypothesis=transcript,
                normalized_hyp=normalized_hyp,
                normalized_expected=normalized_expected,
                confidence=confidence,
                reason="Phrase does not match. One or more words differ.",
            )
        
        # ------- Confidence check (can only tighten, never loosen) -------
        if confidence is not None and confidence < self.confidence_threshold:
            return PhraseResult(
                code="LOW_CONF",
                match=False,
                hypothesis=transcript,
                normalized_hyp=normalized_hyp,
                normalized_expected=normalized_expected,
                confidence=confidence,
                reason=f"Phrase matches but confidence too low ({confidence:.2f} < {self.confidence_threshold:.2f}).",
            )
        
        # ------- All checks passed -------
        return PhraseResult(
            code="OK",
            match=True,
            hypothesis=transcript,
            normalized_hyp=normalized_hyp,
            normalized_expected=normalized_expected,
            confidence=confidence,
            reason="Phrase verified successfully.",
        )


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

# Singleton verifier instance
_default_verifier = PhraseVerifier()


def verify_phrase(
    expected: str,
    transcript: str,
    confidence: Optional[float] = None,
    audio_duration: Optional[float] = None,
    no_speech_prob: Optional[float] = None,
    challenge_expired: bool = False,
    challenge_timed_out: bool = False,
) -> PhraseResult:
    """
    Convenience function using the default PhraseVerifier instance.
    See PhraseVerifier.verify() for full documentation.
    """
    return _default_verifier.verify(
        expected=expected,
        transcript=transcript,
        confidence=confidence,
        audio_duration=audio_duration,
        no_speech_prob=no_speech_prob,
        challenge_expired=challenge_expired,
        challenge_timed_out=challenge_timed_out,
    )
