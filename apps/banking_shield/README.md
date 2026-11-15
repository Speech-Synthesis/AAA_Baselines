# Banking Shield

**AAA Voice Authentication Demo - Banking Application**

Banking Shield demonstrates AAA Engine integration for financial institutions. It provides voice biometric authentication for high-risk banking transactions.

## Features

Per HOST_APPS.md specification:

- Mock login with seeded demo accounts
- Transaction simulation (view balance, transfers, beneficiaries)
- Risk-based step-up authentication
- Voice enrollment via AAA capture
- Voice authentication for high-risk actions
- Fraud/security dashboard
- Audit history

## Quick Start

```bash
# Install dependencies
npm install

# Run in development (mock mode)
npm run dev

# Run with live AAA backend
VITE_USE_MOCK_API=false npm run dev
```

Open http://localhost:5174

## Demo Accounts

| Email | Password | Voice Enrolled |
|-------|----------|----------------|
| alice@bank.demo | demo123 | Yes |
| bob@bank.demo | demo123 | No |
| carol@bank.demo | demo123 | Yes |

## Demo Scenarios

1. **Standard Login**: Sign in with alice@bank.demo / demo123
2. **Voice Enrollment**: Sign in as Bob, navigate to enrollment
3. **High-Risk Transfer**: Create transfer > $10,000, requires voice verification
4. **Voice Authentication**: Navigate to Verify for on-demand voice auth

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_USE_MOCK_API | Use mock API (true) or live backend (false) | true |
| VITE_AAA_API_BASE_URL | AAA Engine API base URL | http://localhost:8000 |

## Tenant Configuration

- Tenant ID: `bank_demo`
- Owner: Karthik
- Peer Reviewer: Surya

## Security Notes

Per HOST_APPS.md:
- No AAA client secrets in frontend code
- Audio captured by AAA component, not stored in frontend
- Only safe policy outcomes exposed (APPROVE/DENY/STEP_UP/REVIEW)
- No raw biometric scores displayed
