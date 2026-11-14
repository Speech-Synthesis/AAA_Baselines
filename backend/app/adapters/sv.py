"""
ECAPA-TDNN Speaker Verification Adapter
Wraps the existing layer1_speaker module.
"""

from .base import ModelInfo, SpeakerResult, SpeakerVerificationAdapter


class EcapaSpeakerAdapter(SpeakerVerificationAdapter):
    """
    Speaker Verification using ECAPA-TDNN via SpeechBrain.

    Embedding dimension: 192
    Score direction: Higher = more similar
    """

    def __init__(self):
        self._model = None
        self._loaded = False

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="ECAPA-TDNN Speaker Verification",
            version="1.0.0",
            model_id="speechbrain/spkrec-ecapa-voxceleb",
            is_loaded=self._loaded,
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        """Load the model (delegated to layer1_speaker on first use)."""
        try:
            # Trigger model loading by calling with minimal audio
            # The actual model is lazily loaded in layer1_speaker
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False

    def unload(self) -> None:
        """Unload the model."""
        # SpeechBrain models are cached globally, not easily unloadable
        self._loaded = False

    def extract_embedding(self, audio_bytes: bytes) -> SpeakerResult:
        """
        Extract 192-dimensional speaker embedding.

        Args:
            audio_bytes: Raw audio data (WAV format)

        Returns:
            SpeakerResult with embedding
        """
        from ..layer1_speaker import enroll_speaker

        result = enroll_speaker(audio_bytes)
        self._loaded = True

        return SpeakerResult(embedding=result["embedding"], score=None, is_match=False)

    def compare_embeddings(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Compare embeddings using cosine similarity.

        Args:
            embedding1: First embedding (192-dim)
            embedding2: Second embedding (192-dim)

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        import numpy as np

        # Convert to numpy arrays
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)

        # Compute cosine similarity
        dot_product = np.dot(e1, e2)
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0, 1] range
        return float(max(0.0, min(1.0, similarity)))

    def verify_speaker(
        self, audio_bytes: bytes, enrolled_embedding: list[float], threshold: float = 0.5
    ) -> SpeakerResult:
        """
        Verify speaker using existing layer1_speaker.verify_speaker.

        Args:
            audio_bytes: Raw audio data
            enrolled_embedding: Enrolled speaker's embedding
            threshold: Minimum similarity for match

        Returns:
            SpeakerResult with score and match status
        """
        from ..layer1_speaker import verify_speaker as l1_verify

        result = l1_verify(audio_bytes, enrolled_embedding)
        self._loaded = True

        return SpeakerResult(
            embedding=result["embedding"],
            score=result["score"],
            is_match=result["score"] >= threshold,
        )
