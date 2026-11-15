# Banking Shield Demo Runbook

## Prerequisites

1. AAA Engine backend running on http://localhost:8000
2. Node.js 18+ installed
3. Modern browser with microphone support

## Setup

```bash
cd apps/banking_shield
npm install
```

## Running the Demo

### Mock Mode (Default)

```bash
npm run dev
```

Opens at http://localhost:5174

### Live Mode (with AAA Backend)

```bash
# Terminal 1: Start AAA backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Start Banking Shield with live API
cd apps/banking_shield
VITE_USE_MOCK_API=false npm run dev
```

## Demo Walkthrough

### Scenario 1: View Dashboard

1. Navigate to http://localhost:5174
2. Login with `alice@bank.demo` / `demo123`
3. View account balances and voice enrollment status
4. Note the "Voice Enrolled" indicator

### Scenario 2: Voice Enrollment (Unenrolled User)

1. Login with `bob@bank.demo` / `demo123`
2. Note the "Voice Not Enrolled" warning
3. Click "Enroll Voice"
4. Read and accept consent
5. Record 3 voice samples speaking the challenge phrases
6. Upon completion, return to dashboard

### Scenario 3: Low-Risk Transfer

1. Login with `alice@bank.demo` / `demo123`
2. Navigate to Transactions
3. Click "New Transfer"
4. Select beneficiary, enter amount < $5,000
5. Transfer approved immediately (LOW risk)

### Scenario 4: High-Risk Transfer with Voice Step-Up

1. Login with `alice@bank.demo` / `demo123`
2. Navigate to Transactions
3. Click "New Transfer"
4. Select beneficiary, enter amount > $10,000
5. Risk assessment shows HIGH risk, STEP_UP required
6. Click "Verify with Voice"
7. Speak the challenge phrase
8. Upon APPROVE, transfer is completed

### Scenario 5: Voice Verification Failure

1. Start a high-risk transfer
2. When recording, speak the wrong phrase or remain silent
3. Observe RETRY or DENY decision
4. Option to try again with fresh challenge

## Demo Scenarios from HOST_APPS.md

| Scenario | Expected Behavior |
|----------|-------------------|
| Enrolled genuine speaker, correct phrase | APPROVE |
| Wrong phrase | DENY |
| Expired/reused challenge | DENY |
| High-risk transaction | STEP_UP |
| Unenrolled user attempts high-risk | Redirect to enrollment |

## Troubleshooting

### Microphone Issues

- Ensure browser has microphone permission
- Check no other app is using the microphone
- Try a different browser (Chrome recommended)

### API Connection Issues

- Verify backend is running: `curl http://localhost:8000/v1/health`
- Check console for CORS errors
- Ensure VITE_AAA_API_BASE_URL is correct

### Voice Verification Failures

- Speak clearly and at normal volume
- Ensure minimal background noise
- Wait for the recording indicator before speaking
- Speak the exact challenge phrase displayed
