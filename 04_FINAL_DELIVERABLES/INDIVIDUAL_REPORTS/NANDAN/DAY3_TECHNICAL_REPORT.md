# Nandan — Day 3 Technical Report

**Date:** November 14, 2026
**Sprint:** Day 3 of 4
**Role:** ASR Lead — Speech Recognition & Phrase Matching
**Branch:** `feat/nandan-asr-callguard` → Merged via PR #15

---

## 1. Executive Summary

Day 3 completed the ASR integration for AAA Engine, implementing phrase verification with fuzzy matching, Word Error Rate (WER) calculation, and Layer 3 risk assessment integration.

**Key Metrics:**
- Phrase matcher tests: 56 passing
- WER threshold: 0.3 (configurable)
- ASR adapter interface: Complete

---

## 2. Deliverables Completed

### 2.1 Phrase Matcher Module

**File:** `aaa_asr/phrase_matcher.py`

| Feature | Implementation |
|---------|----------------|
| Text Normalization | Lowercase, punctuation removal |
| WER Calculation | Levenshtein-based word distance |
| Fuzzy Matching | Configurable threshold |
| Phonetic Fallback | Optional soundex matching |

**Code Sample:**
```python
def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate between reference and hypothesis.

    WER = (S + D + I) / N
    where:
        S = substitutions
        D = deletions
        I = insertions
        N = words in reference
    """
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(hypothesis).split()

    # Dynamic programming for edit distance
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    # ... implementation

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)
```

### 2.2 ASR Adapter Interface

**File:** `aaa_asr/adapters.py`

| Adapter | Purpose |
|---------|---------|
| `ASRAdapter` (Protocol) | Interface definition |
| `MockASRAdapter` | Testing adapter |
| `WhisperAdapter` | Production adapter (stub) |

**Interface Definition:**
```python
class ASRAdapter(Protocol):
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text."""
        ...

    def verify_phrase(
        self,
        audio: np.ndarray,
        expected_phrase: str,
        threshold: float = 0.3
    ) -> tuple[bool, str, float]:
        """
        Verify spoken phrase matches expected.

        Returns:
            - match: True if WER <= threshold
            - transcript: Actual transcription
            - wer: Word Error Rate
        """
        ...
```

### 2.3 Layer 3 ASR Integration

**File:** `backend/app/layer3_asr.py`

| Feature | Implementation |
|---------|----------------|
| Phrase Verification | Integrated with verification pipeline |
| WER Logging | Logged for analysis |
| Threshold Config | Environment-based |

---

## 3. Phrase Matching Algorithm

### 3.1 Text Normalization

```python
def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text
```

### 3.2 WER Calculation

```
Reference: "the quick brown fox"
Hypothesis: "the quick brown dog"

Words: [the, quick, brown, fox] vs [the, quick, brown, dog]

Operations:
- the → the (match)
- quick → quick (match)
- brown → brown (match)
- fox → dog (substitution)

WER = 1/4 = 0.25 (below 0.3 threshold = MATCH)
```

### 3.3 Decision Flow

```
┌──────────────┐
│ Audio Input  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Transcribe  │
│   (Whisper)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Normalize   │
│    Texts     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Calculate    │
│    WER       │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ WER <= 0.3 ?         │
│ Yes → MATCH          │
│ No  → MISMATCH       │
└──────────────────────┘
```

---

## 4. Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_phrase_matcher.py` | 56 | 100% |
| `test_risk_transcript.py` | 4 | 100% |
| **Total** | **60** | **100%** |

### 4.1 Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Exact Match | 8 | Identical phrases |
| Partial Match | 12 | Minor differences |
| No Match | 10 | Significant differences |
| Normalization | 15 | Punctuation, case |
| Edge Cases | 11 | Empty, special chars |

### 4.2 Key Test Cases

```python
# Exact match
def test_exact_match():
    result = verify_phrase(audio, "the quick brown fox")
    assert result.match is True
    assert result.wer == 0.0

# Fuzzy match within threshold
def test_fuzzy_match():
    # Transcribed: "the quick brown dog"
    result = verify_phrase(audio, "the quick brown fox")
    assert result.match is True
    assert result.wer == 0.25

# Mismatch beyond threshold
def test_mismatch():
    # Transcribed: "hello world"
    result = verify_phrase(audio, "the quick brown fox")
    assert result.match is False
    assert result.wer > 0.3
```

---

## 5. Files Created/Modified

### New Files
```
aaa_asr/phrase_matcher.py
aaa_asr/adapters.py
aaa_asr/tests/test_phrase_matcher.py
```

### Modified Files
```
backend/app/layer3_asr.py
aaa_asr/__init__.py
```

---

## 6. Integration Points

| Consumer | Component | Status |
|----------|-----------|--------|
| `v1/verify.py` | `phrase_matcher.py` | ✅ Integrated |
| `layer3_asr.py` | `phrase_matcher.py` | ✅ Integrated |
| Mock Adapters | `adapters.py` | ✅ Available |

---

## 7. Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WER_THRESHOLD` | 0.3 | Max acceptable WER |
| `SAMPLE_RATE` | 16000 | Audio sample rate |
| `ASR_MODEL` | whisper-base | Whisper model size |

---

## 8. Known Limitations

1. **Whisper Integration:** Production Whisper adapter is a stub
2. **Language Support:** Currently English only
3. **Streaming:** No real-time streaming support yet

---

## 9. Day 4 Recommendations

1. Implement production Whisper adapter
2. Add language detection/support
3. Performance optimization for batch processing
4. Add confidence score to phrase verification

---

**Document Version:** 1.0
**Author:** Nandan
**Timestamp:** November 14, 2026
