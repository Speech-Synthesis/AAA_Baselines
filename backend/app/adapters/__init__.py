"""
AAA Engine Model Adapters
Abstraction layer for ML model integration.
"""

from .base import (
    ModelAdapter,
    SpeakerVerificationAdapter,
    DeepfakeDetectionAdapter,
    ASRAdapter,
)
from .sv import EcapaSpeakerAdapter
from .ad import Wav2VecDeepfakeAdapter
from .asr import WhisperASRAdapter
from .mock import (
    MockSpeakerAdapter,
    MockDeepfakeAdapter,
    MockASRAdapter,
)
from .vr import TranscriptRiskAdapter

__all__ = [
    # Base classes
    "ModelAdapter",
    "SpeakerVerificationAdapter",
    "DeepfakeDetectionAdapter",
    "ASRAdapter",
    # Real implementations
    "EcapaSpeakerAdapter",
    "Wav2VecDeepfakeAdapter",
    "WhisperASRAdapter",
    "TranscriptRiskAdapter",
    # Mock implementations
    "MockSpeakerAdapter",
    "MockDeepfakeAdapter",
    "MockASRAdapter",
]
