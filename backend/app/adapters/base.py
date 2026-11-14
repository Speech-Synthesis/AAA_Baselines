"""
AAA Engine Model Adapter Base Classes
Abstract interfaces for model integration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Model metadata."""

    name: str
    version: str
    model_id: str
    is_loaded: bool = False


@dataclass
class SpeakerResult:
    """Result from speaker verification."""

    embedding: list[float]
    score: float | None = None  # Similarity score if comparing
    is_match: bool = False


@dataclass
class DeepfakeResult:
    """Result from deepfake detection."""

    label: str  # "bonafide" or "spoof"
    confidence: float  # 0.0 to 1.0
    is_spoof: bool


@dataclass
class ASRResult:
    """Result from speech recognition."""

    transcript: str
    confidence: float
    similarity: float | None = None  # If comparing to expected phrase


class ModelAdapter(ABC):
    """Base adapter interface for all models."""

    @abstractmethod
    def get_info(self) -> ModelInfo:
        """Get model information."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if model is loaded and ready."""
        pass

    @abstractmethod
    def load(self) -> bool:
        """Load the model. Returns True if successful."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model to free resources."""
        pass


class SpeakerVerificationAdapter(ModelAdapter):
    """
    Adapter interface for Speaker Verification models.

    Responsible for:
    - Extracting voice embeddings
    - Comparing embeddings for speaker similarity
    """

    @abstractmethod
    def extract_embedding(self, audio_bytes: bytes) -> SpeakerResult:
        """
        Extract speaker embedding from audio.

        Args:
            audio_bytes: Raw audio data

        Returns:
            SpeakerResult with embedding vector
        """
        pass

    @abstractmethod
    def compare_embeddings(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Compare two embeddings and return similarity score.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0.0 to 1.0, higher = more similar)
        """
        pass

    def verify_speaker(
        self, audio_bytes: bytes, enrolled_embedding: list[float], threshold: float = 0.5
    ) -> SpeakerResult:
        """
        Verify if audio matches enrolled speaker.

        Args:
            audio_bytes: Raw audio data
            enrolled_embedding: Enrolled speaker's embedding
            threshold: Minimum similarity for match

        Returns:
            SpeakerResult with score and match status
        """
        result = self.extract_embedding(audio_bytes)
        score = self.compare_embeddings(result.embedding, enrolled_embedding)
        return SpeakerResult(embedding=result.embedding, score=score, is_match=score >= threshold)


class DeepfakeDetectionAdapter(ModelAdapter):
    """
    Adapter interface for Deepfake/Spoof Detection models.

    Responsible for:
    - Detecting synthetic or spoofed audio
    """

    @abstractmethod
    def detect(self, audio_bytes: bytes) -> DeepfakeResult:
        """
        Detect if audio is real (bonafide) or fake (spoof).

        Args:
            audio_bytes: Raw audio data

        Returns:
            DeepfakeResult with label and confidence
        """
        pass

    def is_spoof(self, audio_bytes: bytes, threshold: float = 0.5) -> bool:
        """
        Quick check if audio is likely spoofed.

        Args:
            audio_bytes: Raw audio data
            threshold: Minimum confidence to classify as spoof

        Returns:
            True if likely spoofed
        """
        result = self.detect(audio_bytes)
        return result.is_spoof and result.confidence >= threshold


class ASRAdapter(ModelAdapter):
    """
    Adapter interface for Automatic Speech Recognition models.

    Responsible for:
    - Transcribing audio to text
    - Comparing transcriptions to expected phrases
    """

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> ASRResult:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio data

        Returns:
            ASRResult with transcript
        """
        pass

    @abstractmethod
    def compare_phrases(self, transcript: str, expected: str) -> float:
        """
        Compare transcript to expected phrase.

        Args:
            transcript: Transcribed text
            expected: Expected phrase

        Returns:
            Similarity score (0.0 to 1.0)
        """
        pass

    def verify_phrase(
        self, audio_bytes: bytes, expected_phrase: str, threshold: float = 0.6
    ) -> ASRResult:
        """
        Verify if audio contains expected phrase.

        Args:
            audio_bytes: Raw audio data
            expected_phrase: Expected spoken phrase
            threshold: Minimum similarity for match

        Returns:
            ASRResult with similarity score
        """
        result = self.transcribe(audio_bytes)
        similarity = self.compare_phrases(result.transcript, expected_phrase)
        return ASRResult(
            transcript=result.transcript, confidence=result.confidence, similarity=similarity
        )
