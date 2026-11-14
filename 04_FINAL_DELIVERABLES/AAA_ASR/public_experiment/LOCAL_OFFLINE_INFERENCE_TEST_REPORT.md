# AAA-ASR Local Offline Inference & Phrase Matcher Verification Report

**Author:** Nandan (Member 5 — AAA-ASR)  
**Date:** 14 November 2026  
**Execution Environment:** Local CPU (`torch 2.4.1+cpu`)  
**Model Loaded:** Stock OpenAI Whisper `base` staged at `.models/whisper/base.pt`  
**Model Directory:** `E:\AAA_PROJECT\AAA_Baselines\.models\whisper`  
**Status:** COMPLETE — EXECUTED AND VERIFIED  

---

## 1. Execution Evidence & Latency Metrics

- **Audio File Evaluated:** `E:\AAA_PROJECT\datasets\LibriSpeech\LibriSpeech\dev-clean\1272\128104\1272-128104-0000.flac`
- **Audio Duration:** 5.86 seconds
- **Inference Latency:** 4.308 seconds
- **Inference Device:** Local CPU (No CUDA)
- **Network Access:** Zero external network calls (loaded offline from staged weights)
- **Raw ASR Hypothesis:** `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.`
- **Normalized Hypothesis:** `mr quilter is the apostle of the middle classes and we are glad to welcome his gospel`
- **LibriSpeech Book Reference:** `MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES AND WE ARE GLAD TO WELCOME HIS GOSPEL`
- **Normalized Book Reference:** `mister quilter is the apostle of the middle classes and we are glad to welcome his gospel`
- **ASR Confidence:** 0.8043
- **No-Speech Probability:** 0.0074

---

## 2. Phrase Matcher Security Invariants Verification Matrix

| Test Case | Expected Input | Hypothesis Input | Injected Condition | Actual Code | Match Status | Verification Verdict |
|---|---|---|---|---|---|---|
| **Case A (Exact Match)** | `Mr Quilter is the apostle of the middle classes and we are glad to welcome his gospel` | `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.` | Valid, conf=0.90 | `OK` | `True` | **PASS (Exact Match Accepted)** |
| **Case B ('mr' vs 'mister')** | `MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES AND WE ARE GLAD TO WELCOME HIS GOSPEL` | `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.` | Lexical variation | `MISMATCH` | `False` | **PASS (Strict Rejection)** |
| **Case C (Near Miss)** | `Mr Quilter is the apostle of the middle classes and we are glad to welcome his banana` | `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.` | 1 word altered | `MISMATCH` | `False` | **PASS (Near-Miss Rejection)** |
| **Case D (Expired Token)** | `Mr Quilter is the apostle of the middle classes and we are glad to welcome his gospel` | `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.` | `challenge_expired=True` | `EXPIRED_CHALLENGE` | `False` | **PASS (Fail Closed)** |
| **Case E (Low Confidence)** | `Mr Quilter is the apostle of the middle classes and we are glad to welcome his gospel` | `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.` | `confidence=0.30` | `LOW_CONF` | `False` | **PASS (Tightened Gate)** |

---

## 3. Compliance Conclusions

1. Verified that local Whisper models load and transcribe directly from `.models/whisper/base.pt` with zero external network connectivity.
2. Verified strict exact-phrase verification where any word mutation triggers deterministic rejection (`MISMATCH`).
3. Demonstrated zero-fuzzy tolerance: 'mr' versus 'mister' is strictly rejected as `MISMATCH` because fuzzy heuristics are disallowed in authentication.
4. Verified security invariant: confidence scores never turn a textual mismatch into a pass.
5. Verified fail-closed behavior on expired challenge tokens (`EXPIRED_CHALLENGE`).
