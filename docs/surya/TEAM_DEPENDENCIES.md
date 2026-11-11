# AAA Engine — Team Dependencies Tracker

**Version:** 1.0.0
**Date:** November 11, 2026
**Author:** Surya (AAA Core Lead)

---

## Overview

This document tracks all cross-team dependencies required for AAA Engine integration. Each dependency is assigned to an owner and tracked to completion.

---

## Dependency Status Summary

| Owner | Total | Pending | Confirmed | Blocked |
|-------|-------|---------|-----------|---------|
| Navadeep (SV) | 6 | 6 | 0 | 0 |
| Aditya (AD) | 5 | 5 | 0 | 0 |
| Nandan (ASR) | 5 | 5 | 0 | 0 |
| Karthik (VR/Security) | 6 | 6 | 0 | 0 |

---

## Navadeep — AAA-SV (Speaker Verification)

### DEP-SV-001: Inference Interface

| Attribute | Value |
|-----------|-------|
| **Description** | Python async function signature for speaker embedding extraction |
| **Required For** | SpeakerVerificationAdapter implementation |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes — Cannot implement adapter without interface |

**Current Assumption:**
```python
async def extract_embedding(audio_bytes: bytes) -> list[float]:
    """Extract 192-dim speaker embedding."""
    pass
```

---

### DEP-SV-002: Audio Input Contract

| Attribute | Value |
|-----------|-------|
| **Description** | Required audio format, sample rate, duration |
| **Required For** | Input validation |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | No — Using documented defaults |

**Current Assumption:**
- Format: WAV (PCM)
- Sample Rate: 16000 Hz
- Channels: Mono
- Duration: 2-10 seconds

---

### DEP-SV-003: Score Direction

| Attribute | Value |
|-----------|-------|
| **Description** | Whether higher scores indicate same speaker or different speaker |
| **Required For** | Policy engine threshold evaluation |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes — Cannot set correct threshold logic |

**Current Assumption:**
- Higher score = more similar = same speaker
- Score range: [0.0, 1.0]

---

### DEP-SV-004: Embedding Dimension

| Attribute | Value |
|-----------|-------|
| **Description** | Dimensionality of speaker embedding vector |
| **Required For** | Database schema, encryption |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | No — Using 192 from existing code |

**Current Assumption:** 192 dimensions

---

### DEP-SV-005: Threshold Recommendation

| Attribute | Value |
|-----------|-------|
| **Description** | Recommended threshold for accept/reject decision |
| **Required For** | Policy engine configuration |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No — Using 0.5 default |

**Current Assumption:** 0.5 (adjustable)

---

### DEP-SV-006: Model Version/Hash

| Attribute | Value |
|-----------|-------|
| **Description** | Version identifier or hash for model tracking |
| **Required For** | Audit logging, health checks |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | No |

**Current Assumption:** "speechbrain/spkrec-ecapa-voxceleb"

---

## Aditya — AAA-AD (Deepfake Detection)

### DEP-AD-001: Inference Interface

| Attribute | Value |
|-----------|-------|
| **Description** | Python async function signature for deepfake detection |
| **Required For** | DeepfakeDetectionAdapter implementation |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes — Cannot implement adapter without interface |

**Current Assumption:**
```python
async def detect_spoof(audio_bytes: bytes) -> dict:
    """Returns {label: "bonafide"|"spoof", confidence: float}"""
    pass
```

---

### DEP-AD-002: Output Contract

| Attribute | Value |
|-----------|-------|
| **Description** | Exact response format and field names |
| **Required For** | Response parsing |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes |

**Current Assumption:**
```json
{
  "label": "bonafide",
  "confidence": 0.95
}
```

---

### DEP-AD-003: Confidence Semantics

| Attribute | Value |
|-----------|-------|
| **Description** | What does confidence value represent |
| **Required For** | Threshold evaluation |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes |

**Current Assumption:**
- Confidence = probability of predicted label
- For "spoof" with confidence > 0.5: reject

---

### DEP-AD-004: Known Limitations

| Attribute | Value |
|-----------|-------|
| **Description** | Documented model limitations |
| **Required For** | Security documentation |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No |

**Current Assumption:**
- May not detect ElevenLabs, VALL-E, XTTS
- Trained on ASVspoof 2019

---

### DEP-AD-005: Model Version/Hash

| Attribute | Value |
|-----------|-------|
| **Description** | Version identifier for tracking |
| **Required For** | Audit logging |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | No |

**Current Assumption:** "garystafford/wav2vec2-deepfake-voice-detector"

---

## Nandan — AAA-ASR (Speech Recognition)

### DEP-ASR-001: Exact Phrase Contract

| Attribute | Value |
|-----------|-------|
| **Description** | How phrase matching is performed |
| **Required For** | Phrase verification logic |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes |

**Current Assumption:**
- Fuzzy matching with difflib.SequenceMatcher
- Threshold: 0.6 similarity

---

### DEP-ASR-002: Text Normalization

| Attribute | Value |
|-----------|-------|
| **Description** | Text normalization rules for comparison |
| **Required For** | Consistent phrase matching |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | No — Using existing implementation |

**Current Implementation:**
- Lowercase
- Remove punctuation
- Collapse whitespace
- Number words to digits

---

### DEP-ASR-003: Response Schema

| Attribute | Value |
|-----------|-------|
| **Description** | Exact response format |
| **Required For** | Response parsing |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes |

**Current Assumption:**
```python
(is_match: bool, similarity: float, transcript: str)
```

---

### DEP-ASR-004: CallGuard Integration

| Attribute | Value |
|-----------|-------|
| **Description** | How CallGuard will use AAA-ASR |
| **Required For** | Integration architecture |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No |

---

### DEP-ASR-005: Independent Review Schedule

| Attribute | Value |
|-----------|-------|
| **Description** | Nandan's review of Surya's AAA Core work |
| **Required For** | Quality assurance |
| **Status** | PENDING |
| **Target Date** | November 14, 2026 |
| **Blocking** | No |

---

## Karthik — AAA-VR / Security

### DEP-SEC-001: Tenant Authentication Contract

| Attribute | Value |
|-----------|-------|
| **Description** | JWT structure and validation rules |
| **Required For** | Host app authentication |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes — Cannot implement tenant auth |

**Current Assumption:**
- RS256 JWT
- Claims: sub (tenant_id), aud, exp, iat

---

### DEP-SEC-002: JWT Public Keys

| Attribute | Value |
|-----------|-------|
| **Description** | Public keys for JWT validation |
| **Required For** | Signature verification |
| **Status** | PENDING |
| **Target Date** | November 12, 2026 |
| **Blocking** | Yes |

---

### DEP-SEC-003: VR Interface

| Attribute | Value |
|-----------|-------|
| **Description** | Transcript risk analysis interface |
| **Required For** | TranscriptRiskAdapter implementation |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No — Separate service |

---

### DEP-SEC-004: Banking Shield Integration

| Attribute | Value |
|-----------|-------|
| **Description** | How Banking Shield will call AAA |
| **Required For** | API design validation |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No |

---

### DEP-SEC-005: Security Review Schedule

| Attribute | Value |
|-----------|-------|
| **Description** | Security review of AAA Core |
| **Required For** | Production readiness |
| **Status** | PENDING |
| **Target Date** | November 14, 2026 |
| **Blocking** | No |

---

### DEP-SEC-006: Encryption Key Management

| Attribute | Value |
|-----------|-------|
| **Description** | How voiceprint encryption keys are managed |
| **Required For** | Voiceprint encryption |
| **Status** | PENDING |
| **Target Date** | November 13, 2026 |
| **Blocking** | No — Using env var for now |

---

## Action Items for Surya

### Immediate (November 11)

1. [ ] Send dependency list to all owners
2. [ ] Schedule sync call for November 12 AM
3. [ ] Document current assumptions clearly
4. [ ] Create provisional interfaces with warnings

### November 12

1. [ ] Collect confirmations from Navadeep (SV interface)
2. [ ] Collect confirmations from Aditya (AD interface)
3. [ ] Collect confirmations from Nandan (ASR interface)
4. [ ] Collect confirmations from Karthik (Auth contract)
5. [ ] Update adapter implementations based on confirmations

### November 13

1. [ ] Integration testing with actual model outputs
2. [ ] Security review with Karthik
3. [ ] VR interface finalization

### November 14

1. [ ] Independent review with Nandan
2. [ ] Final integration verification
3. [ ] Demo preparation

---

## Communication Log

| Date | Owner | Message | Response |
|------|-------|---------|----------|
| Nov 11 | All | Initial dependency list sent | Pending |

---

**Document Version:** 1.0
**Last Updated:** November 11, 2026
