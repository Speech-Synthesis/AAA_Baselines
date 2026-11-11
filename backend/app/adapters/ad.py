"""
Wav2Vec2 Deepfake Detection Adapter
Wraps the existing layer2_deepfake module.
"""

from .base import DeepfakeDetectionAdapter, DeepfakeResult, ModelInfo


class Wav2VecDeepfakeAdapter(DeepfakeDetectionAdapter):
    """
    Deepfake Detection using Wav2Vec2.

    Labels: "bonafide" (real) or "spoof" (fake)
    Confidence: 0.0 to 1.0 (higher = more confident in label)
    """

    def __init__(self):
        self._model = None
        self._loaded = False

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            name="Wav2Vec2 Deepfake Detection",
            version="1.0.0",
            model_id="wav2vec2-antispoof",
            is_loaded=self._loaded
        )

    def is_ready(self) -> bool:
        return self._loaded

    def load(self) -> bool:
        """Load the model (delegated to layer2_deepfake on first use)."""
        try:
            from ..layer2_deepfake import detect_spoof
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False

    def unload(self) -> None:
        """Unload the model."""
        self._loaded = False

    def detect(self, audio_bytes: bytes) -> DeepfakeResult:
        """
        Detect if audio is real or synthetic.

        Args:
            audio_bytes: Raw audio data (WAV format)

        Returns:
            DeepfakeResult with label and confidence
        """
        from ..layer2_deepfake import detect_spoof

        result = detect_spoof(audio_bytes)
        self._loaded = True

        label = result["label"]
        confidence = result["confidence"]

        return DeepfakeResult(
            label=label,
            confidence=confidence,
            is_spoof=(label == "spoof")
        )
