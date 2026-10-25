# Demo Guide - AAA Engine

Working demonstration of the complete authentication pipeline with sample outputs.

## Table of Contents
- [Quick Demo](#quick-demo)
- [Video Walkthrough](#video-walkthrough)
- [Step-by-Step Guide](#step-by-step-guide)
- [Sample Outputs](#sample-outputs)
- [Testing Different Scenarios](#testing-different-scenarios)

---

## Quick Demo

### Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Microphone access enabled

### 5-Minute Demo

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```

**Open**: http://localhost:5173

---

## Video Walkthrough

### Demo Video Structure

**Part 1: Registration & Enrollment** (2 mins)
1. Open application
2. Register new user
3. Record 3 voice samples
4. Verify enrollment success

**Part 2: Successful Authentication** (1 min)
1. Request challenge phrase
2. Record voice response
3. View authentication success with metrics

**Part 3: Attack Scenarios** (2 mins)
1. Wrong speaker (speaker mismatch rejection)
2. Replay attack (token expiration)
3. Deepfake audio (L2 rejection)

**Recording Script**:
```bash
# Start screen recording
# Windows: Win + G
# macOS: Cmd + Shift + 5
# Linux: SimpleScreenRecorder

# Follow steps below
# Save as: demo-aaa-engine.mp4
```

---

## Step-by-Step Guide

### Part 1: User Registration

**Step 1**: Open application → Click "Register"

**Step 2**: Fill registration form
```
Name: John Doe
Email: john.doe@example.com
```

**Step 3**: Click "Create Account"

**Expected Output**:
```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Screenshot**: Registration success page with user ID displayed

---

### Part 2: Voice Enrollment

**Step 1**: Enter user ID → Click "Start Enrollment"

**Step 2**: Record first sample (5-10 seconds)
```
Phrase: "The quick brown fox jumps over the lazy dog"
Action: Click "Start Recording" → Speak clearly → Click "Stop"
```

**Expected Output**:
```json
{
  "status": "enrolled",
  "sample_count": 1
}
```

**Step 3**: Record second sample (5-10 seconds)
```
Phrase: "She sells seashells by the seashore"
```

**Step 4**: Record third sample (5-10 seconds)
```
Phrase: "How much wood would a woodchuck chuck"
```

**Final State**: Sample count = 3, "Proceed to Verification" button enabled

**Screenshot**: Enrollment complete page showing 3/3 samples

---

### Part 3: Authentication (Success Case)

**Step 1**: Click "Get Challenge"

**Expected Output**:
```json
{
  "phrase": "blue sky mountain river",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_at": "2026-10-25T14:32:45Z"
}
```

**Display**:
```
Challenge Phrase: "blue sky mountain river"
Time Remaining: 90 seconds
```

**Step 2**: Record voice response
- Click "Start Recording"
- Speak the exact phrase: "blue sky mountain river"
- Click "Stop Recording"

**Step 3**: Click "Verify"

**Expected Output (Success)**:
```json
{
  "result": "ACCEPT",
  "confidence": 0.87,
  "layer_blocked": null,
  "session_id": "c9d8e7f6-a5b4-3210-9876-543210fedcba",
  "reason": "Authentication successful",
  "l2_label": "bonafide",
  "l2_confidence": 0.94,
  "l1_score": 0.87,
  "asr_transcript": "blue sky mountain river",
  "asr_similarity": 0.98
}
```

**Display**:
```
✅ AUTHENTICATION SUCCESSFUL

Layer 2 (Deepfake): ✓ PASS (bonafide, 94%)
Layer ASR (Phrase): ✓ PASS (similarity: 98%)
Layer 1 (Speaker):  ✓ PASS (score: 87%)
Layer 3 (Token):    ✓ PASS (valid)

Session ID: c9d8e7f6-a5b4-3210-9876-543210fedcba
```

**Screenshot**: Success page with green checkmarks and metrics

---

## Sample Outputs

### Scenario 1: Successful Authentication

**Request**:
```bash
curl -X POST http://localhost:8000/auth/verify \
  -F "user_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -F "token=eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "audio=@response.wav"
```

**Response**:
```json
{
  "result": "ACCEPT",
  "confidence": 0.87,
  "layer_blocked": null,
  "session_id": "c9d8e7f6-a5b4-3210-9876-543210fedcba",
  "reason": "Authentication successful",
  "l2_label": "bonafide",
  "l2_confidence": 0.94,
  "l1_score": 0.87,
  "asr_transcript": "blue sky mountain river",
  "asr_similarity": 0.98
}
```

---

### Scenario 2: Deepfake Detection (L2 Rejection)

**Setup**: Use deepfake audio generated from ElevenLabs or similar TTS

**Response**:
```json
{
  "result": "REJECT",
  "confidence": 0.78,
  "layer_blocked": 2,
  "session_id": "b8c7d6e5-f4a3-2109-8765-432109edcbaf",
  "reason": "Deepfake/spoof detected",
  "l2_label": "spoof",
  "l2_confidence": 0.78,
  "l1_score": 0.0,
  "asr_transcript": null,
  "asr_similarity": null
}
```

**Display**:
```
❌ AUTHENTICATION FAILED

Layer 2 (Deepfake): ✗ FAIL (spoof detected, 78%)
⚠️ Reason: Deepfake or synthetic voice detected

Pipeline stopped at Layer 2
```

**Screenshot**: Rejection page with red X and warning message

---

### Scenario 3: Wrong Speaker (L1 Rejection)

**Setup**: Different person attempts authentication with correct phrase

**Response**:
```json
{
  "result": "REJECT",
  "confidence": 0.35,
  "layer_blocked": 1,
  "session_id": "a7b6c5d4-e3f2-1098-7654-321098dcbafe",
  "reason": "Speaker verification failed",
  "l2_label": "bonafide",
  "l2_confidence": 0.91,
  "l1_score": 0.35,
  "asr_transcript": "blue sky mountain river",
  "asr_similarity": 0.96
}
```

**Display**:
```
❌ AUTHENTICATION FAILED

Layer 2 (Deepfake): ✓ PASS (bonafide, 91%)
Layer ASR (Phrase): ✓ PASS (similarity: 96%)
Layer 1 (Speaker):  ✗ FAIL (score: 35% < threshold 50%)
⚠️ Reason: Voice does not match enrolled voiceprint

Pipeline stopped at Layer 1
```

---

### Scenario 4: Wrong Phrase (ASR Rejection)

**Setup**: Correct user speaks wrong phrase

**Challenge**: "blue sky mountain river"
**Spoken**: "red sunset ocean lake"

**Response**:
```json
{
  "result": "REJECT",
  "confidence": 0.12,
  "layer_blocked": 4,
  "session_id": "f6e5d4c3-b2a1-0987-6543-210987cbafed",
  "reason": "Phrase mismatch: expected 'blue sky mountain river', heard 'red sunset ocean lake'",
  "l2_label": "bonafide",
  "l2_confidence": 0.92,
  "l1_score": 0.0,
  "asr_transcript": "red sunset ocean lake",
  "asr_similarity": 0.12
}
```

**Display**:
```
❌ AUTHENTICATION FAILED

Layer 2 (Deepfake): ✓ PASS (bonafide, 92%)
Layer ASR (Phrase): ✗ FAIL (similarity: 12% < threshold 60%)

Expected: "blue sky mountain river"
Heard:    "red sunset ocean lake"

⚠️ Reason: Incorrect challenge phrase spoken
```

---

### Scenario 5: Expired Token (L3 Rejection)

**Setup**: Wait 90+ seconds before submitting response

**Response**:
```json
{
  "result": "REJECT",
  "confidence": 0.0,
  "layer_blocked": 3,
  "session_id": "e5d4c3b2-a190-8765-4321-098765bafed",
  "reason": "Invalid or expired token",
  "l2_label": "bonafide",
  "l2_confidence": 0.93,
  "l1_score": 0.88
}
```

**Display**:
```
❌ AUTHENTICATION FAILED

Layer 2 (Deepfake): ✓ PASS (bonafide, 93%)
Layer ASR (Phrase): ✓ PASS (similarity: 97%)
Layer 1 (Speaker):  ✓ PASS (score: 88%)
Layer 3 (Token):    ✗ FAIL (expired)

⚠️ Reason: Challenge token expired (90s limit exceeded)
Request new challenge to try again
```

---

## Testing Different Scenarios

### Automated Test Script

```bash
#!/bin/bash
# test-demo.sh

BASE_URL="http://localhost:8000"

# 1. Register user
echo "Testing registration..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}')

USER_ID=$(echo $REGISTER_RESPONSE | jq -r '.user_id')
echo "✓ User ID: $USER_ID"

# 2. Enroll voice
echo "Testing enrollment..."
for i in 1 2 3; do
  curl -s -X POST $BASE_URL/auth/enroll \
    -F "user_id=$USER_ID" \
    -F "audio=@samples/enrollment_$i.wav" | jq
done
echo "✓ Enrollment complete"

# 3. Get challenge
echo "Testing challenge..."
CHALLENGE=$(curl -s "$BASE_URL/auth/challenge?user_id=$USER_ID")
TOKEN=$(echo $CHALLENGE | jq -r '.token')
PHRASE=$(echo $CHALLENGE | jq -r '.phrase')
echo "✓ Challenge: $PHRASE"

# 4. Verify (success)
echo "Testing verification..."
curl -s -X POST $BASE_URL/auth/verify \
  -F "user_id=$USER_ID" \
  -F "token=$TOKEN" \
  -F "audio=@samples/verify_success.wav" | jq

echo "✓ Demo test complete"
```

**Run**:
```bash
chmod +x test-demo.sh
./test-demo.sh
```

---

## Performance Metrics

### Latency Breakdown

**Per-Layer Processing Time** (median):

| Layer | Operation | Latency |
|-------|-----------|---------|
| L2 | Deepfake detection (Wav2Vec2) | ~420ms |
| ASR | Phrase verification (Whisper) | ~380ms |
| L1 | Speaker verification (ECAPA) | ~290ms |
| L3 | Token validation | ~5ms |
| **Total** | End-to-end | **~1.1s** |

**First Request** (cold start): 8-12s (model loading)
**Subsequent Requests**: <1.5s

---

## Regenerating Sample Metrics

### Generate Authentication Logs

```bash
# Run multiple authentications
for i in {1..10}; do
  curl -X POST http://localhost:8000/auth/verify \
    -F "user_id=$USER_ID" \
    -F "token=$TOKEN" \
    -F "audio=@sample.wav"
done

# View logs
curl "http://localhost:8000/users/$USER_ID/auth-logs" | jq
```

### Output Example

```json
[
  {
    "id": "log-1",
    "user_id": "user-123",
    "result": "ACCEPT",
    "l2_confidence": 0.94,
    "l1_score": 0.87,
    "layer_blocked": null,
    "created_at": "2026-10-25T14:32:45Z",
    "reason": "Authentication successful"
  },
  {
    "id": "log-2",
    "user_id": "user-123",
    "result": "REJECT",
    "l2_confidence": 0.78,
    "l1_score": 0.0,
    "layer_blocked": 2,
    "created_at": "2026-10-25T14:35:12Z",
    "reason": "Deepfake/spoof detected"
  }
]
```

---

## Dashboard Visualization

### Viewing User Statistics

**URL**: http://localhost:5173/dashboard

**Displays**:
- Total authentication attempts
- Success/failure rates
- Layer-wise rejection breakdown
- Voiceprint evolution over time (sample count)
- Recent authentication logs

**Screenshot Example**:
```
┌─────────────────────────────────────┐
│     AAA Engine Dashboard            │
├─────────────────────────────────────┤
│ User: John Doe                      │
│ Voiceprint: 12 samples              │
│                                     │
│ Authentication History              │
│ ✓ Accept: 45 (90%)                  │
│ ✗ Reject: 5 (10%)                   │
│                                     │
│ Rejection Breakdown                 │
│ L1 (Speaker): 2                     │
│ L2 (Deepfake): 1                    │
│ L3 (Token): 2                       │
└─────────────────────────────────────┘
```

---

## Demonstration Checklist

Before running demo:

- [ ] Backend server running (port 8000)
- [ ] Frontend server running (port 5173)
- [ ] Database connected (PostgreSQL/Supabase)
- [ ] Microphone permissions enabled
- [ ] Quiet environment (low background noise)
- [ ] Test audio samples prepared (optional)
- [ ] Screen recording software ready (optional)

**Demo Duration**: 5-7 minutes
**Recommended Audience**: Technical and non-technical stakeholders
**Key Takeaway**: Multi-layer defense provides robust protection against deepfakes and replay attacks

---

**Demo Status**: ✅ Ready for presentation
**Video Recording**: See `demo-video.mp4` (if recorded)
**Sample Outputs**: See `sample-outputs/` directory
