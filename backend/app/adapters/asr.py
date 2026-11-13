"""
Whisper ASR Adapter
Wraps the existing layer3_asr module.
"""

from .base import ASRAdapter, ASRResult, ModelInfo


class WhisperASRAdapter(ASRAdapter):
    """
    Automatic Speech Recognition using OpenAI Whisper.

    Supports phrase comparison using sequence matching.
    """

    def __init__(self, model_name: str = "base"):
        self._model = None
        self._loaded = False
        self._model_name = model_name

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="Whisper ASR",
            version="1.0.0",
            model_id=f"openai/whisper-{self._model_name}",
            is_loaded=self._loaded
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        """Load the model (delegated to layer3_asr on first use)."""
        try:
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False

    def unload(self) -> None:
        """Unload the model."""
        self._loaded = False

    def transcribe(self, audio_bytes: bytes) -> ASRResult:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Raw audio data (WAV format)

        Returns:
            ASRResult with transcript
        """
        from ..layer3_asr import verify_phrase

        # Use verify_phrase with empty expected to just get transcript
        _, _, transcript = verify_phrase(audio_bytes, "", 0.0)
        self._loaded = True

        return ASRResult(
            transcript=transcript or "",
            confidence=1.0,  # Whisper doesn't provide per-result confidence
            similarity=None
        )

    def compare_phrases(
        self,
        transcript: str,
        expected: str
    ) -> float:
        """
        Compare transcript to expected phrase using sequence matching.

        Args:
            transcript: Transcribed text
            expected: Expected phrase

        Returns:
            Similarity score (0.0 to 1.0)
        """
        from difflib import SequenceMatcher

        if not transcript or not expected:
            return 0.0

        # Normalize both strings
        t1 = transcript.lower().strip()
        t2 = expected.lower().strip()

        # Use SequenceMatcher for fuzzy comparison
        return SequenceMatcher(None, t1, t2).ratio()

    def verify_phrase(
        self,
        audio_bytes: bytes,
        expected_phrase: str,
        threshold: float = 0.6
    ) -> ASRResult:
        """
        Verify if audio contains expected phrase.

        Uses existing layer3_asr.verify_phrase for consistency.

        Args:
            audio_bytes: Raw audio data
            expected_phrase: Expected spoken phrase
            threshold: Minimum similarity for match

        Returns:
            ASRResult with similarity score
        """
        from ..layer3_asr import verify_phrase as l3_verify

        is_match, similarity, transcript = l3_verify(
            audio_bytes, expected_phrase, threshold
        )
        self._loaded = True

        return ASRResult(
            transcript=transcript or "",
            confidence=1.0,
            similarity=similarity
        )
