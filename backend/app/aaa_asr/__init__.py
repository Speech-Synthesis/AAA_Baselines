"""
AAA-ASR — Challenge Phrase Recognition + Verification Module

This module provides:
- PhraseVerifier: Deterministic exact-match phrase verification after safe normalization
- Transcriber: Local Whisper ASR wrapper (separate from verification logic)

Architecture: ASR transcribes. Matcher decides. Keep separate.
"""

from .phrase_matcher import PhraseVerifier, PhraseResult, normalize_text
from .transcriber import Transcriber

__all__ = ["PhraseVerifier", "PhraseResult", "normalize_text", "Transcriber"]
