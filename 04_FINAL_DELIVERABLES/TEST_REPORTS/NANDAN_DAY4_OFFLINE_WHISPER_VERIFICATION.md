# AAA-ASR Local Offline Whisper Verification Report (Day 4)

**Document ID:** `NANDAN_DAY4_OFFLINE_WHISPER_VERIFICATION`  
**Execution Timestamp:** 2026-11-15T00:30:35+05:30  
**Verification Lead:** Nandan (Member 5 — AAA-ASR & CallGuard Lead)  
**Role:** Member 5  
**Target Repository:** `E:\AAA_PROJECT\AAA_Baselines`  
**Active Branch:** `feat/nandan-asr-callguard-day2`  
**Commit HEAD:** `f7bc9cd9e80b5ea8420078394d65be5fc6f8417f` (`Merge pull request #18 from Speech-Synthesis/feat/nandan-asr-callguard-day2`)  
**Mode:** STRICT READ-ONLY AUDIT & VERIFICATION  

---

## 1. Executive Summary & Verdict

| Verification Item | Specification / Expectation | Observed Execution Result | Status / Verdict |
|:---|:---|:---|:---|
| **Model Weight Staging** | Local Whisper `base.pt` on E: drive | `E:\AAA_PROJECT\AAA_Baselines\.models\whisper\base.pt` (145,262,807 bytes) | **VERIFIED** |
| **Model Checksum** | Official OpenAI Whisper base SHA-256 | `ED3A0B6B1C0EDF879AD9B11B1AF5A0E6AB5DB9205F891F668F8B0E6C6326E34E` | **VERIFIED** |
| **Network Isolation** | Zero network calls; no cloud API usage | Whisper loaded strictly from local disk (`download_root` on E: drive) | **VERIFIED (OFFLINE)** |
| **Model Download Attempts** | 0 bytes downloaded | Default cache (`C:\Users\DELL\.cache\whisper`) empty; zero downloads | **VERIFIED (0 BYTES)** |
| **Transcription Accuracy** | High-fidelity transcript on clean audio | `"Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel."` | **VERIFIED** |
| **Inference Latency** | Local CPU inference | 5.021 seconds (audio duration: 5.86 seconds) | **VERIFIED (< 1.0x Real-time)** |
| **Phrase Verifier Integration** | Exact-match security policy | 5/5 security cases validated (Exact match: `OK`; Mutations: `MISMATCH`) | **VERIFIED (PASS)** |
| **Final Step 1 Verdict** | **PASS** | Fully compliant with Day 4 Offline Whisper mandates | **PASS** |

---

## 2. Environment & Dependency Audit

The offline inference test was executed using the primary project virtual environment on the `E:` drive containing PyTorch and `openai-whisper`.

### 2.1 Python Runtime
- **Python Executable:** `E:\AAA_PROJECT\AAA_Baselines\.venv\Scripts\python.exe`
- **Python Version:** `Python 3.8.2` (64-bit Windows)
- **Secondary Environment (.venv311):** `E:\AAA_PROJECT\AAA_Baselines\.venv311\Scripts\python.exe` (`Python 3.11.9`) maintained for phrase matcher unit tests.

### 2.2 Installed Audio & ML Dependencies (.venv)
- `openai-whisper`: `20250625`
- `torch`: `2.4.1+cpu`
- `soundfile`: `0.13.1`
- `numpy`: `1.24.4`
- `numba`: `0.58.1`
- `tiktoken`: `0.7.0`
- `tqdm`: `4.70.1`

---

## 3. Staged Model Artifact Verification

Direct inspection of the staged weight files under `E:\AAA_PROJECT\AAA_Baselines\.models\whisper` confirmed:

```powershell
Get-Item "E:\AAA_PROJECT\AAA_Baselines\.models\whisper\base.pt" | Select-Object FullName, Length, LastWriteTime
```
- **Full Path:** `E:\AAA_PROJECT\AAA_Baselines\.models\whisper\base.pt`
- **File Size:** `145,262,807 bytes` (~138.53 MB)
- **SHA-256 Checksum:** `ED3A0B6B1C0EDF879AD9B11B1AF5A0E6AB5DB9205F891F668F8B0E6C6326E34E`
- **Reference URL Check:** Matches OpenAI base model hash:
  `https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt`

---

## 4. Test Script & Sample Audio Identification

The pre-existing inference test script created by Member 5 was identified and audited on disk:
- **Test Script Path:** `E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\AAA_ASR\public_experiment\local_offline_inference_test.py`
- **Audio Evaluation Sample:** `E:\AAA_PROJECT\datasets\LibriSpeech\LibriSpeech\dev-clean\1272\128104\1272-128104-0000.flac`
  - Audio Format: 16-bit FLAC, 16,000 Hz, Mono
  - Audio Duration: 5.86 seconds
  - Book Reference: `"MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES AND WE ARE GLAD TO WELCOME HIS GOSPEL"`

---

## 5. Execution Command and Terminal Output

### 5.1 Exact Execution Command
```powershell
Set-Location "E:\AAA_PROJECT\AAA_Baselines"
$env:WHISPER_MODEL_DIR = "E:\AAA_PROJECT\AAA_Baselines\.models\whisper"

.\.venv\Scripts\python.exe 04_FINAL_DELIVERABLES/AAA_ASR/public_experiment/local_offline_inference_test.py `
    "E:\AAA_PROJECT\datasets\LibriSpeech\LibriSpeech\dev-clean\1272\128104\1272-128104-0000.flac" `
    "MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES AND WE ARE GLAD TO WELCOME HIS GOSPEL" `
    "E:\AAA_PROJECT\AAA_Baselines\04_FINAL_DELIVERABLES\TEST_REPORTS\NANDAN_DAY4_OFFLINE_WHISPER_VERIFICATION.md"
```

### 5.2 Captured Terminal Execution Output
```text
=================================================================
>>> AAA-ASR LOCAL OFFLINE INFERENCE & VERIFIER TEST <<<
=================================================================
[Offline Test] Staged Whisper Model Directory: E:\AAA_PROJECT\AAA_Baselines\.models\whisper
[Offline Test] Transcribing audio sample: 1272-128104-0000.flac ...
[AAA-ASR] Loading Whisper model: base on cpu
[AAA-ASR] Whisper model loaded successfully
[Offline Test] ASR Output: 'Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.'
[Offline Test] Duration: 5.86s | Latency: 5.021s | Confidence: 0.804
[Case A: Exact Match] Decision: OK (match=True) | Reason: Phrase verified successfully.
[Case B: Strict Rejection of 'mr' vs 'mister'] Decision: MISMATCH (match=False) | Reason: Phrase does not match. One or more words differ.
[Case C: Near-Miss Rejection] Decision: MISMATCH (match=False) | Reason: Phrase does not match. One or more words differ.
[Case D: Expired Challenge] Decision: EXPIRED_CHALLENGE (match=False) | Reason: Challenge has expired. A new challenge is required.
[Case E: Low Confidence] Decision: LOW_CONF (match=False) | Reason: Phrase matches but confidence too low (0.30 < 0.50).
```

---

## 6. Offline Verification Evidence & Security Invariant Matrix

### 6.1 Transcription Metrics
- **Raw Whisper Hypothesis:** `Mr. Quilter is the apostle of the middle classes, and we are glad to welcome his gospel.`
- **Normalized Hypothesis:** `mr quilter is the apostle of the middle classes and we are glad to welcome his gospel`
- **Calculated Confidence:** `0.8043`
- **No-Speech Probability:** `0.0074`
- **Inference Latency:** `5.021 seconds` (CPU runtime)

### 6.2 Security Policy Cases
| Case ID | Expected Phrase | Input Hypothesis | Condition Tested | Code | Match Status | Verification Result |
|:---|:---|:---|:---|:---|:---|:---|
| **Case A** | `Mr Quilter is the apostle of the middle classes and we are glad to welcome his gospel` | `Mr. Quilter is the apostle...` | Exact match normalized, high conf (0.90) | `OK` | `True` | **PASS (Exact Match Accepted)** |
| **Case B** | `MISTER QUILTER IS THE APOSTLE...` | `Mr. Quilter is the apostle...` | Lexical difference (`mr` vs `mister`) | `MISMATCH` | `False` | **PASS (Zero Fuzzy Tolerance)** |
| **Case C** | `...and we are glad to welcome his banana` | `Mr. Quilter is the apostle...` | 1 word substituted near miss | `MISMATCH` | `False` | **PASS (Near Miss Rejected)** |
| **Case D** | `Mr Quilter is the apostle...` | `Mr. Quilter is the apostle...` | `challenge_expired=True` | `EXPIRED_CHALLENGE` | `False` | **PASS (Fail Closed)** |
| **Case E** | `Mr Quilter is the apostle...` | `Mr. Quilter is the apostle...` | Low confidence gate (`confidence=0.30`) | `LOW_CONF` | `False` | **PASS (Tightened Policy)** |

---

## 7. Audit Compliance Statement

1. **No External Network Activity:** Model weights were loaded directly from local path on `E:` drive. No network requests were initiated during transcription.
2. **Zero Unauthorized File Modifications:** Only this report file (`NANDAN_DAY4_OFFLINE_WHISPER_VERIFICATION.md`) was written. Source code, configuration, Git branches, and teammate-owned directories remain 100% untouched.
3. **Reproducibility:** All paths, script invocations, hashes, and timings are documented for independent verification.
