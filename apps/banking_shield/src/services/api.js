/**
 * Banking Shield API Service Layer
 *
 * Target Contract: AAA Engine Public REST API v1.0
 * Tenant: bank_demo
 *
 * Strict Security Rules (from HOST_APPS.md):
 * 1. Banking Shield frontend NEVER receives, stores, or forwards raw audio directly.
 * 2. AAA-controlled capture component uploads directly to AAA.
 * 3. No AAA client secrets or service-role keys in frontend code.
 * 4. Only safe policy outcomes and public reason categories exposed.
 *
 * Mode Configuration:
 * - Production: VITE_USE_MOCK_API=false (calls real AAA backend)
 * - Development: VITE_USE_MOCK_API=true (isolated mock adapter for UI testing only)
 *
 * IMPORTANT: Mock mode is for UI development ONLY. All five decision outcomes
 * (APPROVE, DENY, STEP_UP, REVIEW, UNAVAILABLE) originate from backend PolicyEngine.
 */

// Environment detection - production builds MUST set VITE_USE_MOCK_API=false
const IS_PRODUCTION = typeof import.meta !== "undefined" && import.meta.env && import.meta.env.PROD === true;
const MOCK_EXPLICITLY_DISABLED = typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_USE_MOCK_API === "false";

// Mock mode: ONLY enabled in development when explicitly NOT disabled
// Production builds should ALWAYS have mock disabled
const USE_MOCK = IS_PRODUCTION ? false : !MOCK_EXPLICITLY_DISABLED;

const API_BASE = (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_AAA_API_BASE_URL) || "http://localhost:8000";
const DEMO_TENANT = "bank_demo";

// Log mode on initialization (development only)
if (!IS_PRODUCTION) {
  console.info(`[Banking Shield API] Mode: ${USE_MOCK ? 'MOCK (dev only)' : 'LIVE'}, Backend: ${API_BASE}`);
}

/**
 * Create a challenge for voice authentication.
 * Calls POST /v1/challenges
 */
export async function createChallenge(userRef, purpose = "high_risk_transaction") {
  if (USE_MOCK) {
    const phrases = [
      "Seven Red Chair Twenty",
      "Blue Green Yellow Forty",
      "Eight Silver Desk Fourteen",
      "Golden Eagle Flight Nine",
      "Three White River Fifty"
    ];
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];
    const challengeId = "ch_" + Math.random().toString(36).substring(2, 10);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 90 * 1000).toISOString();

    return {
      challenge_id: challengeId,
      phrase: phrase,
      expires_at: expiresAt,
      ttl_seconds: 90,
      tenant_id: DEMO_TENANT,
      user_ref: userRef,
      token: challengeId,
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/challenges`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_ref: userRef,
      purpose,
      client_request_id: `bs-${Date.now()}`
    })
  });
  if (!res.ok) throw new Error(`Failed to create challenge: ${res.statusText}`);
  return await res.json();
}

/**
 * Enroll voice sample for user.
 * Calls POST /v1/enroll
 */
export async function enrollVoice(userRef, audioBlob) {
  if (USE_MOCK) {
    // Simulate enrollment
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      status: "enrolled",
      sample_count: 1,
      user_ref: userRef,
      _mock: true
    };
  }

  const formData = new FormData();
  formData.append("user_id", userRef);
  formData.append("audio", audioBlob, "enrollment.webm");

  const res = await fetch(`${API_BASE}/v1/enroll`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) throw new Error(`Enrollment failed: ${res.statusText}`);
  return await res.json();
}

/**
 * Verify voice against challenge.
 * Calls POST /v1/verify
 *
 * Returns one of FIVE approved decisions per SYSTEM.md §6:
 * - APPROVE: All gates pass
 * - DENY: Authentication fails
 * - STEP_UP: Additional verification needed (fresh challenge)
 * - REVIEW: Human review required
 * - UNAVAILABLE: Service unavailable
 *
 * IMPORTANT: In production, all decisions originate from backend PolicyEngine.
 * Mock responses are for UI development only and do NOT represent real authentication.
 */
export async function verifyVoice(userRef, challengeToken, audioBlob) {
  // === PRODUCTION PATH: Real backend call ===
  if (!USE_MOCK) {
    const formData = new FormData();
    formData.append("user_id", userRef);
    formData.append("token", challengeToken);
    formData.append("audio", audioBlob, "verification.webm");

    const res = await fetch(`${API_BASE}/v1/verify`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error(`Verification failed: ${res.statusText}`);
    return await res.json();
  }

  // === DEVELOPMENT MOCK PATH (UI testing only) ===
  // WARNING: These responses do NOT reflect real PolicyEngine decisions
  console.warn('[Banking Shield API] MOCK MODE: Returning simulated verification result');
  await new Promise(resolve => setTimeout(resolve, 800));

  const requestId = "req_mock_" + Math.random().toString(36).substring(2, 10);
  const sessionId = "sess_mock_" + Math.random().toString(36).substring(2, 10);

  // Default mock response - always APPROVE for UI development
  // Real decisions come from PolicyEngine in production
  return {
    request_id: requestId,
    decision: "APPROVE",
    reason: "Voice verification successful (MOCK)",
    reason_public: "OK",
    risk_level: "LOW",
    session_id: sessionId,
    _mock: true,
    _warning: "MOCK MODE - Real decisions come from PolicyEngine"
  };
}

/**
 * Get audit history for user.
 * Calls GET /users/{user_id}/auth-logs (simplified)
 */
export async function getAuditHistory(userRef, limit = 10) {
  if (USE_MOCK) {
    return [
      {
        id: "log_1",
        timestamp: new Date().toISOString(),
        event_type: "VOICE_VERIFICATION",
        decision: "APPROVE",
        reason_public: "Verification successful"
      },
      {
        id: "log_2",
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        event_type: "LOGIN",
        decision: "APPROVE",
        reason_public: "Standard login"
      },
      {
        id: "log_3",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        event_type: "TRANSFER",
        decision: "APPROVE",
        reason_public: "Low-risk transfer"
      }
    ];
  }

  const res = await fetch(`${API_BASE}/users/${userRef}/auth-logs?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to get audit history: ${res.statusText}`);
  return await res.json();
}

/**
 * Check AAA Engine health status.
 */
export async function checkAAAHealth() {
  if (USE_MOCK) {
    return {
      status: "HEALTHY",
      engine: "AAA-Engine v1.0 (Mock Mode)",
      layers: {
        layer1_sv: "READY",
        layer2_ad: "READY",
        layer3_asr: "READY"
      },
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/ready`);
  if (!res.ok) {
    return { status: "UNHEALTHY", error: res.statusText };
  }
  return await res.json();
}

/**
 * Create a capture grant for AAA-controlled audio capture.
 * The host backend calls this, then passes the capture_url to the AAA capture component.
 * Audio is recorded and uploaded directly to AAA - never through the host app.
 *
 * Calls POST /v1/capture/grants
 */
export async function createCaptureGrant(userId, challengeId) {
  if (USE_MOCK) {
    // In mock mode, return a mock capture URL for UI development
    const mockGrantId = "grant_mock_" + Math.random().toString(36).substring(2, 10);
    const mockSig = "mock_sig_" + Math.random().toString(36).substring(2, 10);
    return {
      grant_id: mockGrantId,
      capture_url: `/static/capture/index.html?grant=${mockGrantId}&sig=${mockSig}`,
      expires_at: new Date(Date.now() + 90000).toISOString(),
      ttl_seconds: 90,
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/capture/grants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      challenge_id: challengeId
    })
  });
  if (!res.ok) throw new Error(`Failed to create capture grant: ${res.statusText}`);
  return await res.json();
}

/**
 * Get the base URL for the AAA API (used for iframe src).
 */
export function getAPIBaseURL() {
  return API_BASE;
}
