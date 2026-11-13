"""
AAA Engine Model Adapters
Abstraction layer for ML model integration.
"""

from .ad import Wav2VecDeepfakeAdapter
from .asr import WhisperASRAdapter
from .base import (
    ASRAdapter,
    DeepfakeDetectionAdapter,
    ModelAdapter,
    SpeakerVerificationAdapter,
)
from .mock import (
    MockASRAdapter,
    MockDeepfakeAdapter,
    MockSpeakerAdapter,
)
from .sv import EcapaSpeakerAdapter

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
    # Mock implementations
    "MockSpeakerAdapter",
    "MockDeepfakeAdapter",
    "MockASRAdapter",
]
