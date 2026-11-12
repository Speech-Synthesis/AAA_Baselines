# AAA Engine — Model Adapter Contracts

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)
**Status:** PROVISIONAL — Pending owner confirmation

---

## Overview

This document defines the adapter interfaces for all model components in AAA Engine. Adapters abstract model implementation details from the orchestration layer, enabling:

1. Model replacement without API changes
2. Mock implementations for testing
3. Health/version reporting
4. Consistent error handling
5. Timeout policies

---

## Base Adapter Interface

All model adapters implement this common interface:

```python
from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime

TRequest = TypeVar('TRequest', bound=BaseModel)
TResponse = TypeVar('TResponse', bound=BaseModel)


class ModelHealth(BaseModel):
    """Health status for a model adapter."""
    available: bool
    model_id: str
    version: Optional[str] = None
    loaded_at: Optional[datetime] = None
    last_inference: Optional[datetime] = None
    error: Optional[str] = None


class ModelAdapter(ABC, Generic[TRequest, TResponse]):
    """Base interface for all model adapters."""

    @abstractmethod
    async def health(self) -> ModelHealth:
        """Check if the model is available and healthy."""
        pass

    @abstractmethod
    async def predict(self, request: TRequest) -> TResponse:
        """Execute model inference."""
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier."""
        pass

    @property
    def timeout_seconds(self) -> float:
        """Return the inference timeout in seconds."""
        return 10.0
```

---

## AAA-SV: Speaker Verification Adapter

**Owner:** Navadeep
**Status:** PROVISIONAL — Interface pending owner confirmation

### Request Schema

```python
class SpeakerVerificationRequest(BaseModel):
    """Input for speaker verification."""
    audio_bytes: bytes  # 16kHz mono WAV
    stored_embedding: Optional[list[float]] = None  # 192-dim, None for enrollment

    class Config:
        arbitrary_types_allowed = True
```

### Response Schema

```python
class SpeakerVerificationResponse(BaseModel):
    """Output from speaker verification."""
    embedding: list[float]  # 192-dimensional
    score: Optional[float] = None  # Cosine similarity [0, 1], None for enrollment
    model_version: str
```

### Interface

```python
class SpeakerVerificationAdapter(ModelAdapter[SpeakerVerificationRequest, SpeakerVerificationResponse]):
    """Adapter for AAA-SV (Speaker Verification)."""

    async def health(self) -> ModelHealth:
        """Check ECAPA-TDNN model availability."""
        ...

    async def predict(self, request: SpeakerVerificationRequest) -> SpeakerVerificationResponse:
        """
        Extract speaker embedding and optionally compute similarity.

        If stored_embedding is None: enrollment mode (extract only)
        If stored_embedding provided: verification mode (extract + compare)
        """
        ...

    @property
    def model_id(self) -> str:
        return "speechbrain/spkrec-ecapa-voxceleb"
```

### Score Semantics

| Score Range | Interpretation |
|-------------|----------------|
| 0.75 - 1.0 | Same speaker (high confidence) |
| 0.50 - 0.75 | Same speaker (moderate confidence) |
| 0.30 - 0.50 | Uncertain |
| 0.0 - 0.30 | Different speaker |

**PENDING CONFIRMATION:** Score direction (higher = more similar) and threshold recommendations.

---

## AAA-AD: Deepfake Detection Adapter

**Owner:** Aditya
**Status:** PROVISIONAL — Interface pending owner confirmation

### Request Schema

```python
class DeepfakeDetectionRequest(BaseModel):
    """Input for deepfake detection."""
    audio_bytes: bytes  # 16kHz mono WAV

    class Config:
        arbitrary_types_allowed = True
```

### Response Schema

```python
class DeepfakeLabel(str, Enum):
    """Classification labels for deepfake detection."""
    BONAFIDE = "bonafide"  # Real human speech
    SPOOF = "spoof"  # Synthetic/AI-generated speech


class DeepfakeDetectionResponse(BaseModel):
    """Output from deepfake detection."""
    label: DeepfakeLabel
    confidence: float  # Probability [0, 1]
    model_version: str
```

### Interface

```python
class DeepfakeDetectionAdapter(ModelAdapter[DeepfakeDetectionRequest, DeepfakeDetectionResponse]):
    """Adapter for AAA-AD (Deepfake Detection)."""

    async def health(self) -> ModelHealth:
        """Check Wav2Vec2 model availability."""
        ...

    async def predict(self, request: DeepfakeDetectionRequest) -> DeepfakeDetectionResponse:
        """
        Classify audio as bonafide or spoof.

        Returns label with confidence probability.
        """
        ...

    @property
    def model_id(self) -> str:
        return "garystafford/wav2vec2-deepfake-voice-detector"
```

### Confidence Semantics

- `confidence` is the probability of the predicted label
- For `spoof` label with `confidence > 0.5`: reject audio
- For `bonafide` label with `confidence > 0.5`: accept audio

**PENDING CONFIRMATION:** Threshold tuning and known model limitations.

### Known Limitations (Documented)

The current model may not reliably detect:
- Modern high-quality TTS (ElevenLabs, VALL-E, XTTS)
- Real-time voice conversion
- Adversarially crafted audio

---

## AAA-ASR: Speech Recognition Adapter

**Owner:** Nandan
**Status:** PROVISIONAL — Interface pending owner confirmation

### Request Schema

```python
class ASRRequest(BaseModel):
    """Input for speech recognition."""
    audio_bytes: bytes  # 16kHz mono WAV
    expected_phrase: str  # Challenge phrase to match

    class Config:
        arbitrary_types_allowed = True
```

### Response Schema

```python
class ASRResponse(BaseModel):
    """Output from speech recognition."""
    transcript: str  # Raw transcribed text
    normalized_transcript: str  # Normalized for comparison
    expected_normalized: str  # Normalized expected phrase
    similarity: float  # Similarity score [0, 1]
    match: bool  # Whether similarity >= threshold
    model_version: str
```

### Interface

```python
class ASRAdapter(ModelAdapter[ASRRequest, ASRResponse]):
    """Adapter for AAA-ASR (Speech Recognition)."""

    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold

    async def health(self) -> ModelHealth:
        """Check Whisper model availability."""
        ...

    async def predict(self, request: ASRRequest) -> ASRResponse:
        """
        Transcribe audio and compare to expected phrase.

        Normalization includes:
        - Lowercase
        - Remove punctuation
        - Collapse whitespace
        - Number word to digit conversion
        """
        ...

    @property
    def model_id(self) -> str:
        return "openai/whisper-base"
```

### Similarity Calculation

- Uses `difflib.SequenceMatcher.ratio()`
- Returns value between 0.0 (no match) and 1.0 (exact match)
- Default threshold: 0.6

**PENDING CONFIRMATION:** Threshold tuning and exact matching requirements.

---

## AAA-VR: Transcript Risk Adapter

**Owner:** Karthik
**Status:** PROVISIONAL — Interface pending owner confirmation

### Request Schema

```python
class TranscriptRiskRequest(BaseModel):
    """Input for transcript risk analysis."""
    session_id: str
    transcript: str
    context: Optional[dict] = None  # call_type, claimed_identity, etc.
```

### Response Schema

```python
class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TranscriptRiskResponse(BaseModel):
    """Output from transcript risk analysis."""
    risk_level: RiskLevel
    risk_indicators: list[str]  # Detected risk patterns
    recommended_action: str  # APPROVE, DENY, STEP_UP, REVIEW
    confidence: float
    model_version: str
```

### Interface

```python
class TranscriptRiskAdapter(ModelAdapter[TranscriptRiskRequest, TranscriptRiskResponse]):
    """Adapter for AAA-VR (Transcript Risk Analysis)."""

    async def health(self) -> ModelHealth:
        """Check risk analysis model availability."""
        ...

    async def predict(self, request: TranscriptRiskRequest) -> TranscriptRiskResponse:
        """
        Analyze transcript for vishing/fraud indicators.

        Risk indicators may include:
        - urgent_transfer_request
        - account_number_mentioned
        - pressure_tactics_detected
        - impersonation_attempt
        """
        ...

    @property
    def model_id(self) -> str:
        return "aaa-vr/transcript-risk-v1"  # TBD
```

**NOTE:** AAA-VR is a separate analysis service for CallGuard. It does NOT participate in speaker verification decisions.

---

## Mock Adapters

For development and testing, mock adapters are provided:

```python
class MockSpeakerVerificationAdapter(SpeakerVerificationAdapter):
    """Mock adapter for testing."""

    def __init__(self, should_pass: bool = True, score: float = 0.85):
        self._should_pass = should_pass
        self._score = score

    async def health(self) -> ModelHealth:
        return ModelHealth(
            available=True,
            model_id="mock/sv",
            version="mock-1.0"
        )

    async def predict(self, request: SpeakerVerificationRequest) -> SpeakerVerificationResponse:
        return SpeakerVerificationResponse(
            embedding=[0.0] * 192,
            score=self._score if request.stored_embedding else None,
            model_version="mock-1.0"
        )

    @property
    def model_id(self) -> str:
        return "mock/sv"
```

**IMPORTANT:** Mock adapters must clearly identify themselves and NEVER be used in production.

---

## Error Handling

All adapters should raise typed exceptions:

```python
class ModelError(Exception):
    """Base exception for model errors."""
    pass


class ModelNotAvailableError(ModelError):
    """Model is not loaded or available."""
    pass


class ModelInferenceError(ModelError):
    """Error during inference."""
    pass


class ModelTimeoutError(ModelError):
    """Inference exceeded timeout."""
    pass
```

---

## Pending Owner Confirmations

| Adapter | Owner | Required Confirmation |
|---------|-------|----------------------|
| AAA-SV | Navadeep | Score direction, threshold, embedding dim |
| AAA-AD | Aditya | Confidence semantics, known limitations |
| AAA-ASR | Nandan | Similarity threshold, normalization rules |
| AAA-VR | Karthik | Risk indicators, response format |

---

**Document Version:** 1.0
**Classification:** Interface Contract
