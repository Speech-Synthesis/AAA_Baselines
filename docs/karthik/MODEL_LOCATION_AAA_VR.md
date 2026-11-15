# AAA-VR Model Location & Architecture Specification

**Component**: Work Package No. 8 — `AAA-VR - Vishing Risk Engine`  
**Owner**: Karthik Mallareddy (`KarthikMallareddy <mrkarthik1811@gmail.com>`)  
**Role**: Security, AAA-VR & Banking Shield Architect  
**Model Name**: AAA-VR Transcript Risk Engine  
**Model ID**: `aaa-vr/transcript-risk-v1`  
**Version**: `1.0.0`  

---

## 1. Approved Project Architecture Mapping

Per the approved project work packages:
- **Work Package**: **No. 8**
- **Model / Component**: **`AAA-VR – Vishing Risk Engine`**
- **Owner**: **Karthik**
- **Function**: **Detect scam and social-engineering patterns in call transcripts and generate risk scores.**

---

## 2. Model File Locations

### A. Pretrained Model Directory
Consistent with other project models (such as `spkrec-ecapa-voxceleb`), the AAA-VR model files are stored in:
- Primary location: `backend/pretrained_models/aaa-vr/`
  - `config.json`: Hyperparameters, versioning, confidence thresholds, and categorical mappings.
  - `patterns.json`: Lexical pattern definitions and regex extractors for 6 fraud classes.
  - `README.md`: Model card and documentation.
- Mirror root location: `pretrained_models/aaa-vr/`

### B. Implementation Code Locations
- **Model Adapter**: `backend/app/adapters/vr.py`
  - Class: `TranscriptRiskAdapter` (inherits from `ModelAdapter`)
  - Inference method: `analyze_transcript(transcript)` and `predict(request, request_id)`
- **REST API Endpoint**: `backend/app/api/v1/risk.py`
  - Route: `POST /v1/risk/transcript`
  - Security: Protected by tenant-scoped Bearer JWT and sliding-window rate limiters.
- **Data Schemas**: `backend/app/schemas/risk.py`
  - Classes: `TranscriptRiskRequest`, `TranscriptRiskResponse`, `RiskLevel`, `RiskIndicator`, `RiskAction`
- **Unit Test Suite**: `backend/tests/test_risk_transcript.py`
  - 4 comprehensive test scenarios covering benign calls, wire fraud, credential harvesting, and direct endpoint execution.

---

## 3. Operational Characteristics
- **Inference Latency**: $< 5\text{ ms}$ (in-memory optimized regex evaluation).
- **Output Contract**: Categorical decision (`APPROVE` / `REVIEW` / `STEP_UP` / `DENY`), risk level (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`), and frozen public reason codes.
- **Privacy & Redaction**: Zero-retention memory processing; PII is scrubbed before audit logging.
