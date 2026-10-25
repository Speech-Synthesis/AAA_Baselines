# Demo Guide

Step-by-step walkthrough of AAA Engine's authentication pipeline with sample outputs.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Authentication Workflow](#authentication-workflow)
- [Step 1: User Registration](#step-1-user-registration)
- [Step 2: Voice Enrollment](#step-2-voice-enrollment)
- [Step 3: Authentication](#step-3-authentication)
- [Rejection Scenarios](#rejection-scenarios)
- [API Examples](#api-examples)
- [Performance Notes](#performance-notes)

---

## Prerequisites

Before running the demo:

1. Backend running on `http://localhost:8000`
2. Frontend running on `http://localhost:5173`
3. Microphone access enabled in browser
4. Quiet environment (low background noise)

**Starting the Application:**

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

## Authentication Workflow

```
+----------------+     +----------------+     +----------------+
|                |     |                |     |                |
|   Register     | --> |    Enroll      | --> |    Verify      |
|   (one-time)   |     |   (3+ samples) |     |   (per login)  |
|                |     |                |     |                |
+----------------+     +----------------+     +----------------+
```

---

## Step 1: User Registration

### Process

1. Open http://localhost:5173
2. Navigate to Register page
3. Enter name and email
4. Submit registration

### Input

| Field | Value |
|-------|-------|
| Name | John Doe |
| Email | john.doe@example.com |

### API Request

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john.doe@example.com"}'
```

### Response

```json
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Notes

- Save the `user_id` for subsequent steps
- Email must be unique in the system
- Registration is a one-time process

---

## Step 2: Voice Enrollment

### Process

1. Navigate to Enroll page
2. Enter user_id from registration
3. Record voice sample (5-10 seconds)
4. Submit sample
5. Repeat for 3+ samples

### Recording Guidelines

| Guideline | Reason |
|-----------|--------|
| Speak naturally | System learns your normal voice |
| 5-10 second clips | Sufficient audio for embedding |
| Quiet environment | Reduces noise interference |
| Vary your phrases | Captures voice characteristics |
| Record 3+ samples | Improves voiceprint accuracy |

### Sample Phrases for Enrollment

```
Sample 1: "The quick brown fox jumps over the lazy dog."
Sample 2: "She sells seashells by the seashore."
Sample 3: "How much wood would a woodchuck chuck."
```

### API Request

```bash
curl -X POST http://localhost:8000/auth/enroll \
  -F "user_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -F "audio=@enrollment_sample.wav"
```

### Response

```json
{
  "status": "enrolled",
  "sample_count": 1
}
```

After 3 samples:

```json
{
  "status": "enrolled",
  "sample_count": 3
}
```

---

## Step 3: Authentication

### Process

1. Navigate to Verify page
2. Enter user_id
3. Click "Get Challenge" to receive phrase
4. Read the challenge phrase aloud
5. Submit recording

### Challenge Response

When requesting a challenge:

```json
{
  "phrase": "blue sky mountain river",
  "token": "8f3a2b1c4d5e6f7890abcdef12345678...",
  "expires_at": "2024-01-15T14:32:45Z"
}
```

### Verification Process

```
Audio Recording
       |
       v
+------------------+
| Layer 2:         |
| Deepfake Check   |
| Result: bonafide |
| Confidence: 94%  |
+--------+---------+
         |
         v
+------------------+
| ASR Layer:       |
| Phrase Match     |
| Transcript:      |
| "blue sky        |
|  mountain river" |
| Similarity: 98%  |
+--------+---------+
         |
         v
+------------------+
| Layer 1:         |
| Speaker Match    |
| Score: 87%       |
+--------+---------+
         |
         v
+------------------+
| Layer 3:         |
| Token Valid      |
| Not Expired      |
| Not Used         |
+--------+---------+
         |
         v
    ACCEPT
```

### Successful Response

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

## Rejection Scenarios

### Scenario 1: Deepfake Detected (Layer 2)

**Cause:** AI-generated or synthetic audio submitted

**Response:**

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

**Interpretation:**
- Pipeline stopped at Layer 2
- No speaker verification performed (security measure)
- Audio flagged as synthetic with 78% confidence

---

### Scenario 2: Wrong Phrase (ASR Layer)

**Cause:** User spoke different phrase than challenge

**Challenge:** "blue sky mountain river"
**Spoken:** "red sunset ocean lake"

**Response:**

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

**Interpretation:**
- Passed deepfake check (bonafide)
- Failed phrase verification
- 12% similarity indicates completely different phrase

---

### Scenario 3: Speaker Mismatch (Layer 1)

**Cause:** Different person attempting authentication

**Response:**

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

**Interpretation:**
- Passed deepfake check
- Correct phrase spoken (96% similarity)
- Speaker score (35%) below threshold (50%)
- Voice does not match enrolled voiceprint

---

### Scenario 4: Expired Token (Layer 3)

**Cause:** More than 90 seconds elapsed since challenge

**Response:**

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

**Interpretation:**
- All audio checks passed
- Token expired (90-second TTL exceeded)
- Request new challenge and retry

---

## API Examples

### Complete Authentication Flow

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

# Step 1: Register
echo "Registering user..."
REGISTER=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}')

USER_ID=$(echo $REGISTER | jq -r '.user_id')
echo "User ID: $USER_ID"

# Step 2: Enroll (repeat 3 times with different audio)
echo "Enrolling voice samples..."
for i in 1 2 3; do
  curl -s -X POST $BASE_URL/auth/enroll \
    -F "user_id=$USER_ID" \
    -F "audio=@samples/enrollment_$i.wav"
  echo ""
done

# Step 3: Get Challenge
echo "Getting challenge..."
CHALLENGE=$(curl -s "$BASE_URL/auth/challenge?user_id=$USER_ID")
TOKEN=$(echo $CHALLENGE | jq -r '.token')
PHRASE=$(echo $CHALLENGE | jq -r '.phrase')
echo "Phrase: $PHRASE"

# Step 4: Verify
echo "Verifying..."
curl -s -X POST $BASE_URL/auth/verify \
  -F "user_id=$USER_ID" \
  -F "token=$TOKEN" \
  -F "audio=@samples/verify.wav" | jq
```

### Viewing Authentication Logs

```bash
curl -s "http://localhost:8000/users/$USER_ID/auth-logs" | jq
```

**Response:**

```json
[
  {
    "id": "log-uuid-1",
    "user_id": "user-uuid",
    "l2_label": "bonafide",
    "l2_confidence": 0.94,
    "l1_score": 0.87,
    "result": "ACCEPT",
    "layer_blocked": null,
    "created_at": "2024-01-15T14:32:45Z",
    "reason": "Authentication successful"
  },
  {
    "id": "log-uuid-2",
    "user_id": "user-uuid",
    "l2_label": "spoof",
    "l2_confidence": 0.78,
    "l1_score": 0.0,
    "result": "REJECT",
    "layer_blocked": 2,
    "created_at": "2024-01-15T14:35:12Z",
    "reason": "Deepfake/spoof detected"
  }
]
```

---

## Performance Notes

### Latency

| Operation | First Request | Subsequent |
|-----------|---------------|------------|
| Register | ~50ms | ~50ms |
| Enroll | ~8-12s (cold) | ~500ms |
| Challenge | ~50ms | ~50ms |
| Verify | ~10-15s (cold) | ~1.1s |

First requests load ML models into memory. Subsequent requests reuse cached models.

### Audio Requirements

| Property | Requirement |
|----------|-------------|
| Format | WAV |
| Sample Rate | 16kHz (auto-resampled) |
| Channels | Mono (auto-converted) |
| Duration (Enroll) | 5-10 seconds |
| Duration (Verify) | 2-5 seconds |

### Tips for Best Results

1. Use consistent microphone for enrollment and verification
2. Maintain similar distance from microphone
3. Speak at natural pace and volume
4. Minimize background noise
5. Enroll multiple samples for robust voiceprint

---

## Demo Checklist

Before demonstration:

- [ ] Backend server running (port 8000)
- [ ] Frontend server running (port 5173)
- [ ] Database accessible
- [ ] Microphone connected and tested
- [ ] Quiet environment
- [ ] Browser microphone permission granted

**Demo Duration:** 5-7 minutes

---

**Demo Guide Version:** 1.0
