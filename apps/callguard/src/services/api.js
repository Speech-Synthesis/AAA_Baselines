/**
 * CallGuard API Service Layer
 * 
 * Target Contract: AAA Engine Public REST API v1.0
 * Specified in 03_SYSTEM_REFERENCES/API_SPECIFICATION.md
 * 
 * Strict Security Rules:
 * 1. CallGuard frontend NEVER receives, stores, or forwards raw audio.
 * 2. AAA-controlled capture component uploads directly to AAA over /v1/verify.
 * 3. No AAA client secrets or service-role keys are placed in frontend code.
 * 4. Mode: Configurable Mock Adapter (Day 1 Integration Preparation).
 */

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== "false"; // Defaults to true for Day 1
const API_BASE = import.meta.env.VITE_AAA_API_BASE_URL || "http://localhost:8000";
const DEMO_TENANT = "callcentre_demo";

/**
 * Request a fresh challenge session from AAA.
 * Calls POST /v1/challenges
 * 
 * @param {string} userRef - Pseudonymous user identifier (e.g. "customer_001")
 * @param {string} purpose - Purpose of challenge (e.g. "callcentre_auth")
 */
export async function createChallenge(userRef, purpose = "callcentre_high_risk_verification") {
  if (USE_MOCK) {
    // Deterministic mock generation matching AAA contract
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
      capture: {
        component: "aaa-web-capture",
        upload_url: `${API_BASE}/v1/verify`,
        capture_grant: "grant_mock_jwt_token_" + Math.random().toString(36).substring(2, 14)
      },
      _mock: true
    };
  }

  // Real backend proxy call (Host backend to AAA)
  const res = await fetch(`${API_BASE}/v1/challenges`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_ref: userRef,
      purpose,
      client_request_id: `cg-${Date.now()}`
    })
  });
  if (!res.ok) throw new Error(`Failed to create challenge: ${res.statusText}`);
  return await res.json();
}

/**
 * Poll or fetch verification request outcome.
 * Calls GET /v1/verification-requests/{request_id}
 * 
 * @param {string} requestId
 */
export async function getVerificationResult(requestId) {
  if (USE_MOCK) {
    return {
      request_id: requestId,
      decision: "APPROVE",
      reason_public: "REQUIRED_CHECKS_PASSED",
      risk_level: "LOW",
      api_version: "v1",
      timestamp: new Date().toISOString(),
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/verification-requests/${requestId}`);
  if (!res.ok) throw new Error(`Verification status query failed: ${res.statusText}`);
  return await res.json();
}

/**
 * Submit transcript segments to AAA-VR for vishing and social engineering risk analysis.
 * Calls POST /v1/risk/transcript
 * 
 * @param {Array<{speaker: string, text: string, timestamp: string}>} segments
 */
export async function analyzeTranscriptRisk(segments) {
  if (USE_MOCK) {
    const combinedText = segments.map(s => s.text.toLowerCase()).join(" ");
    
    // Hard negative check: Genuine security advisory from bank agent
    if (combinedText.includes("never share your otp") || combinedText.includes("fraud prevention unit")) {
      return {
        risk_level: "LOW",
        reason_public: "SECURITY_AWARENESS_WARNING",
        recommended_action: "NONE",
        detected_triggers: [],
        timestamp: new Date().toISOString(),
        _mock: true
      };
    }

    // High risk triggers (urgency + credential solicitation)
    if (combinedText.includes("bypass") || combinedText.includes("terminate") || (combinedText.includes("otp") && combinedText.includes("immediately"))) {
      return {
        risk_level: "HIGH",
        reason_public: "URGENT_CREDENTIAL_SOLICITATION",
        recommended_action: "ESCALATE_HUMAN_REVIEW",
        detected_triggers: ["URGENCY_PRESSURE", "CREDENTIAL_COERCION"],
        timestamp: new Date().toISOString(),
        _mock: true
      };
    }

    // Standard low risk default
    return {
      risk_level: "LOW",
      reason_public: "ROUTINE_INQUIRY",
      recommended_action: "NONE",
      detected_triggers: [],
      timestamp: new Date().toISOString(),
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/risk/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tenant_id: DEMO_TENANT,
      segments
    })
  });
  if (!res.ok) throw new Error(`Vishing risk analysis failed: ${res.statusText}`);
  return await res.json();
}

/**
 * Check AAA health and readiness status
 */
export async function checkAAAHealth() {
  if (USE_MOCK) {
    return {
      status: "HEALTHY",
      engine: "AAA-Engine v1.0 (Mock Adapter)",
      layers: {
        layer1_sv: "READY",
        layer2_ad: "READY",
        layer3_asr: "READY",
        layer3_phrase_verifier: "DETERMINISTIC_EXACT_MATCH"
      },
      _mock: true
    };
  }

  const res = await fetch(`${API_BASE}/v1/ready`);
  return await res.json();
}
