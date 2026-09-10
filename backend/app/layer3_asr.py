"""
Layer 3 — Speech-to-Text (ASR) for Challenge Phrase Verification
Uses OpenAI Whisper to transcribe audio and verify spoken phrase matches expected challenge.
"""

import io
import os
import sys
import tempfile
import difflib
import re
from typing import Tuple

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import torch
import whisper
import soundfile as sf
import numpy as np

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
        print(f"[L3-ASR] Whisper model loaded successfully")
    return _whisper_model


def _normalize_text(text: str) -> str:
    """
    Normalize text for comparison:
    - Lowercase
    - Remove punctuation
    - Collapse whitespace
    - Convert number words to digits and vice versa
    """
    text = text.lower().strip()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    # Normalize numbers: convert words to digits for consistent comparison
    number_map = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    for word, digit in number_map.items():
        text = re.sub(rf'\b{word}\b', digit, text)

    return text


def _extract_phrase_content(challenge_phrase: str) -> str:
    """
    Extract the content to match from challenge phrase.
    Handles "Say: X Y Z" format by removing the "Say:" prefix.
    """
    phrase = challenge_phrase.strip()
    if phrase.lower().startswith("say:"):
        phrase = phrase[4:].strip()
    return _normalize_text(phrase)


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity ratio between two texts.
    Returns value between 0.0 (no match) and 1.0 (exact match).
    """
    return difflib.SequenceMatcher(None, text1, text2).ratio()


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
    result = model.transcribe(
        audio_data,
        language="en",
        fp16=torch.cuda.is_available()
    )

    transcript = result.get("text", "").strip()
    # Safe print for Windows console
    try:
        print(f"[L3-ASR] Transcribed: '{transcript}'")
    except UnicodeEncodeError:
        print(f"[L3-ASR] Transcribed: '{transcript.encode('ascii', 'replace').decode()}'")
    return transcript


def verify_phrase(audio_bytes: bytes, expected_phrase: str, threshold: float = 0.6) -> Tuple[bool, float, str]:
    """
    Verify that spoken audio matches expected challenge phrase.

    Args:
        audio_bytes: Raw WAV audio bytes
        expected_phrase: The challenge phrase the user should speak
        threshold: Minimum similarity score to accept (0.0-1.0)

    Returns:
        Tuple of (is_match, similarity_score, transcribed_text)
    """
    try:
        # Transcribe the audio
        transcribed = transcribe_audio(audio_bytes)

        # Normalize both texts for comparison
        expected_normalized = _extract_phrase_content(expected_phrase)
        transcribed_normalized = _normalize_text(transcribed)

        try:
            print(f"[L3-ASR] Expected (normalized): '{expected_normalized}'")
            print(f"[L3-ASR] Transcribed (normalized): '{transcribed_normalized}'")
        except UnicodeEncodeError:
            print("[L3-ASR] (Unicode print error - continuing)")

        # Calculate similarity
        similarity = _calculate_similarity(expected_normalized, transcribed_normalized)
        print(f"[L3-ASR] Phrase similarity: {similarity:.3f} (threshold: {threshold})")

        is_match = similarity >= threshold

        return is_match, similarity, transcribed

    except Exception as e:
        print(f"[L3-ASR] Error during transcription: {e}")
        # On error, return False with 0 similarity
        return False, 0.0, f"[ASR Error: {str(e)}]"
