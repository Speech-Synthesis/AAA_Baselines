"""
Mock Model Adapters for Testing
Deterministic implementations that don't require ML models.
"""

import random

from .base import (
    ASRAdapter,
    ASRResult,
    DeepfakeDetectionAdapter,
    DeepfakeResult,
    ModelInfo,
    SpeakerResult,
    SpeakerVerificationAdapter,
)


class MockSpeakerAdapter(SpeakerVerificationAdapter):
    """
    Mock Speaker Verification for testing.

    Generates deterministic embeddings based on input.
    """

    def __init__(self, default_score: float = 0.75, embedding_dim: int = 192):
        self._default_score = default_score
        self._embedding_dim = embedding_dim
        self._loaded = True
        self._call_count = 0

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="Mock Speaker Verification",
            version="1.0.0-mock",
            model_id="mock/speaker-verification",
            is_loaded=self._loaded,
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        self._loaded = True
        return True

    def unload(self) -> None:
        self._loaded = False

    def extract_embedding(self, audio_bytes: bytes) -> SpeakerResult:
        """Generate deterministic embedding from audio hash."""
        self._call_count += 1

        # Use audio length as seed for reproducibility
        seed = len(audio_bytes) % 1000
        random.seed(seed)

        embedding = [random.gauss(0, 1) for _ in range(self._embedding_dim)]

        return SpeakerResult(embedding=embedding, score=None, is_match=False)

    def compare_embeddings(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Return default score for testing."""
        return self._default_score

    def verify_speaker(
        self, audio_bytes: bytes, enrolled_embedding: list[float], threshold: float = 0.5
    ) -> SpeakerResult:
        """Return configurable verification result."""
        result = self.extract_embedding(audio_bytes)
        return SpeakerResult(
            embedding=result.embedding,
            score=self._default_score,
            is_match=self._default_score >= threshold,
        )

    def set_score(self, score: float) -> None:
        """Configure the mock score for testing."""
        self._default_score = score


class MockDeepfakeAdapter(DeepfakeDetectionAdapter):
    """
    Mock Deepfake Detection for testing.

    Configurable to return bonafide or spoof.
    """

    def __init__(self, default_label: str = "bonafide", default_confidence: float = 0.95):
        self._default_label = default_label
        self._default_confidence = default_confidence
        self._loaded = True
        self._call_count = 0

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="Mock Deepfake Detection",
            version="1.0.0-mock",
            model_id="mock/deepfake-detection",
            is_loaded=self._loaded,
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        self._loaded = True
        return True

    def unload(self) -> None:
        self._loaded = False

    def detect(self, audio_bytes: bytes) -> DeepfakeResult:
        """Return configured detection result."""
        self._call_count += 1

        return DeepfakeResult(
            label=self._default_label,
            confidence=self._default_confidence,
            is_spoof=(self._default_label == "spoof"),
        )

    def set_result(self, label: str, confidence: float = 0.95) -> None:
        """Configure the mock result for testing."""
        self._default_label = label
        self._default_confidence = confidence


class MockASRAdapter(ASRAdapter):
    """
    Mock ASR for testing.

    Returns configurable transcript.
    """

    def __init__(self, default_transcript: str | None = None, default_similarity: float = 0.9):
        self._default_transcript = default_transcript
        self._default_similarity = default_similarity
        self._loaded = True
        self._call_count = 0

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="Mock ASR", version="1.0.0-mock", model_id="mock/asr", is_loaded=self._loaded
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        self._loaded = True
        return True

    def unload(self) -> None:
        self._loaded = False

    def transcribe(self, audio_bytes: bytes) -> ASRResult:
        """Return configured transcript."""
        self._call_count += 1

        transcript = self._default_transcript or "mock transcript"

        return ASRResult(transcript=transcript, confidence=1.0, similarity=None)

    def compare_phrases(self, transcript: str, expected: str) -> float:
        """Return configured similarity."""
        return self._default_similarity

    def verify_phrase(
        self, audio_bytes: bytes, expected_phrase: str, threshold: float = 0.6
    ) -> ASRResult:
        """Return configured verification result."""
        self._call_count += 1

        # If transcript not set, use expected phrase for perfect match
        transcript = self._default_transcript or expected_phrase

        return ASRResult(transcript=transcript, confidence=1.0, similarity=self._default_similarity)

    def set_transcript(self, transcript: str) -> None:
        """Configure the mock transcript for testing."""
        self._default_transcript = transcript

    def set_similarity(self, similarity: float) -> None:
        """Configure the mock similarity for testing."""
        self._default_similarity = similarity
