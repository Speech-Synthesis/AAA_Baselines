"""
Layer 3 — Speech-to-Text (ASR) for Challenge Phrase Verification
Uses OpenAI Whisper to transcribe audio and verify spoken phrase matches expected challenge.
Updated for AAA Engine Day 1: Integrates with aaa_asr deterministic exact phrase matcher.
"""

from __future__ import annotations

import io
import os
import sys

import numpy as np
import soundfile as sf
import torch
import whisper

# Integration with approved AAA-ASR deterministic phrase matcher
from .aaa_asr.phrase_matcher import normalize_text as aaa_normalize_text
from .aaa_asr.phrase_matcher import verify_phrase as aaa_verify_phrase

# Fix Windows console encoding issues
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, io.UnsupportedOperation, OSError):
        pass

# Whisper model - use "base" for good balance of speed/accuracy
# Options: tiny, base, small, medium, large
_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
_whisper_model = None


def _get_whisper_model():
    """Lazy load Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        print(f"[L3-ASR] Loading Whisper model: {_MODEL_SIZE}")
        _whisper_model = whisper.load_model(_MODEL_SIZE)
        print("[L3-ASR] Whisper model loaded successfully")
    return _whisper_model


def _extract_phrase_content(challenge_phrase: str) -> str:
    """
    Extract the content to match from challenge phrase.
    Handles "Say: X Y Z" format by removing the "Say:" prefix.
    """
    phrase = challenge_phrase.strip()
    if phrase.lower().startswith("say:"):
        phrase = phrase[4:].strip()
    return aaa_normalize_text(phrase)


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using Whisper.

    Args:
        audio_bytes: Raw WAV audio bytes (16kHz mono expected)

    Returns:
        Transcribed text
    """
    model = _get_whisper_model()

    # Load audio from bytes
    audio_io = io.BytesIO(audio_bytes)
    audio_data, sample_rate = sf.read(audio_io)

    # Whisper expects float32 audio normalized to [-1, 1]
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)

    # If stereo, convert to mono
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Resample to 16kHz if needed (Whisper requires 16kHz)
    if sample_rate != 16000:
        from scipy import signal

        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = signal.resample(audio_data, num_samples)

    # Whisper transcription
    result = model.transcribe(audio_data, language="en", fp16=torch.cuda.is_available())

    transcript = result.get("text", "").strip()
    # Safe print for Windows console
    try:
        print(f"[L3-ASR] Transcribed: '{transcript}'")
    except UnicodeEncodeError:
        print(f"[L3-ASR] Transcribed: '{transcript.encode('ascii', 'replace').decode()}'")
    return transcript


def verify_phrase(
    audio_bytes: bytes, expected_phrase: str, threshold: float = 0.6
) -> tuple[bool, float, str]:
    """
    Verify that spoken audio matches expected challenge phrase.
    Updated for Day 1: Uses deterministic exact matching after safe normalization.
    No fuzzy SequenceMatcher acceptance in the authentication path.

    Args:
        audio_bytes: Raw WAV audio bytes
        expected_phrase: The challenge phrase the user should speak
        threshold: Ignored for authentication (exact match required); preserved for backward compatibility.

    Returns:
        Tuple of (is_match, similarity_score, transcribed_text)
    """
    try:
        # Transcribe the audio
        transcribed = transcribe_audio(audio_bytes)

        # Use approved deterministic exact-match phrase verifier
        result = aaa_verify_phrase(expected=expected_phrase, transcript=transcribed)

        # In deterministic mode: 1.0 for exact match, 0.0 for mismatch
        score = 1.0 if result.match else 0.0
        print(f"[L3-ASR] Deterministic result: {result.code} (match={result.match})")

        return result.match, score, transcribed

    except Exception as e:
        print(f"[L3-ASR] Error during transcription: {e}")
        # On error, return False with 0 similarity
        return False, 0.0, f"[ASR Error: {str(e)}]"
