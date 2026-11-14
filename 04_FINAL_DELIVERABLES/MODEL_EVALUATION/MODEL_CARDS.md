# AAA Engine — Model Cards

**Date:** November 14, 2026
**Version:** 1.0

---

## 1. L1 Speaker Verification Model

### Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | Speaker Embedding Extractor |
| **Task** | Speaker verification via embedding comparison |
| **Architecture** | Configurable via adapter interface |
| **Input** | Audio waveform (16kHz, mono) |
| **Output** | 256-dimensional embedding vector |

### Performance Metrics

| Metric | Value | Threshold |
|--------|-------|-----------|
| EER (Equal Error Rate) | Target < 5% | Production |
| FAR (False Accept Rate) | Configurable | 0.01 default |
| FRR (False Reject Rate) | Configurable | 0.05 default |
| Cosine Similarity Threshold | 0.7 | Configurable |

### Adapter Interface

```python
class SpeakerAdapter(Protocol):
    def enroll_speaker(self, audio: np.ndarray) -> list[float]:
        """Extract speaker embedding for enrollment."""
        ...

    def verify_speaker(
        self,
        audio: np.ndarray,
        enrolled_embedding: list[float]
    ) -> float:
        """Return similarity score between 0 and 1."""
        ...
```

### Mock Implementation

| Function | Behavior |
|----------|----------|
| `enroll_speaker` | Returns fixed 256-dim embedding |
| `verify_speaker` | Returns configurable similarity score |

---

## 2. L2 Deepfake Detection Model

### Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | Audio Spoof Detector |
| **Task** | Distinguish bonafide vs spoofed audio |
| **Architecture** | Configurable via adapter interface |
| **Input** | Audio waveform (16kHz, mono) |
| **Output** | Classification (bonafide/spoof) + confidence |

### Performance Metrics

| Metric | Value | Dataset |
|--------|-------|---------|
| Detection Accuracy | Target > 95% | ASVspoof |
| False Positive Rate | < 5% | Production |
| Latency | < 100ms | Streaming |

### Adapter Interface

```python
class SpoofAdapter(Protocol):
    def detect_spoof(self, audio: np.ndarray) -> tuple[str, float]:
        """
        Returns:
            - label: "bonafide" or "spoof"
            - confidence: 0.0 to 1.0
        """
        ...
```

### Mock Implementation

| Function | Behavior |
|----------|----------|
| `detect_spoof` | Returns configurable bonafide/spoof |

---

## 3. ASR Phrase Verification Model

### Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | Speech-to-Text + Phrase Matcher |
| **Task** | Transcribe audio and match against expected phrase |
| **Architecture** | Whisper-based (configurable) |
| **Input** | Audio waveform (16kHz, mono) + expected phrase |
| **Output** | Match decision + transcript |

### Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| WER (Word Error Rate) | Target < 10% | Clean audio |
| Phrase Match Threshold | WER < 0.3 | Fuzzy matching |
| Latency | < 500ms | Depends on audio length |

### Adapter Interface

```python
class ASRAdapter(Protocol):
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text."""
        ...

    def verify_phrase(
        self,
        audio: np.ndarray,
        expected_phrase: str
    ) -> tuple[bool, str, float]:
        """
        Returns:
            - match: True if phrase matches
            - transcript: Actual transcription
            - wer: Word error rate
        """
        ...
```

### Phrase Matching Algorithm

```python
def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Word Error Rate = (S + D + I) / N
    where:
        S = substitutions
        D = deletions
        I = insertions
        N = words in reference
    """
```

### Mock Implementation

| Function | Behavior |
|----------|----------|
| `transcribe` | Returns configurable transcript |
| `verify_phrase` | Returns configurable match result |

---

## 4. L3 Risk Assessment Model

### Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | Risk Decision Engine |
| **Task** | Aggregate layer outputs into final decision |
| **Architecture** | Rule-based engine |
| **Input** | Layer outputs (L1, L2, ASR) |
| **Output** | Decision (APPROVE/REJECT/REVIEW) |

### Decision Matrix

| L2 (Spoof) | ASR (Phrase) | L1 (Speaker) | Decision |
|------------|--------------|--------------|----------|
| bonafide | match | pass | APPROVE |
| bonafide | match | fail | REJECT |
| bonafide | mismatch | any | REJECT |
| spoof | any | any | REJECT |

### Risk Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Spoof Detection | Critical | Immediate reject if spoof |
| Phrase Mismatch | High | Reject if phrase doesn't match |
| Speaker Mismatch | High | Reject if speaker verification fails |
| Challenge Expiry | Medium | Reject if token expired |

---

## 5. Adapter Configuration

### Production Adapters

| Layer | Adapter Class | Model |
|-------|---------------|-------|
| L1 | `ProductionSpeakerAdapter` | TBD |
| L2 | `ProductionSpoofAdapter` | TBD |
| ASR | `WhisperAdapter` | Whisper-base |

### Test/Mock Adapters

| Layer | Adapter Class | Purpose |
|-------|---------------|---------|
| L1 | `MockSpeakerAdapter` | Unit testing |
| L2 | `MockSpoofAdapter` | Unit testing |
| ASR | `MockASRAdapter` | Unit testing |

---

## 6. Model Versioning

| Model | Current Version | Last Updated |
|-------|-----------------|--------------|
| Speaker Adapter Interface | v1.0 | 2026-11-14 |
| Spoof Adapter Interface | v1.0 | 2026-11-14 |
| ASR Adapter Interface | v1.0 | 2026-11-14 |
| Risk Engine | v1.0 | 2026-11-14 |

---

**Document Version:** 1.0
**Author:** Surya
**Timestamp:** November 14, 2026
