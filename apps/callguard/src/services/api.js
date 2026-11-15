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
const DEMO_TENANT = "callcentre_demo";

// Log mode on initialization (development only)
if (!IS_PRODUCTION) {
  console.info(`[CallGuard API] Mode: ${USE_MOCK ? 'MOCK (dev only)' : 'LIVE'}, Backend: ${API_BASE}`);
}

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
 * Returns one of FIVE approved decisions per SYSTEM.md §6:
 * - APPROVE: All gates pass
 * - DENY: Authentication fails
 * - STEP_UP: Additional verification needed (fresh challenge)
 * - REVIEW: Human review required
 * - UNAVAILABLE: Service unavailable
 *
 * IMPORTANT: In production, all decisions originate from backend PolicyEngine.
 * Mock responses are for UI development only and do NOT represent real authentication.
 *
 * @param {string} requestId
 */
export async function getVerificationResult(requestId) {
  // === PRODUCTION PATH: Real backend call ===
  if (!USE_MOCK) {
    const res = await fetch(`${API_BASE}/v1/verification-requests/${requestId}`);
    if (!res.ok) throw new Error(`Verification status query failed: ${res.statusText}`);
    return await res.json();
  }

  // === DEVELOPMENT MOCK PATH (UI testing only) ===
  // WARNING: These responses do NOT reflect real PolicyEngine decisions
  console.warn('[CallGuard API] MOCK MODE: Returning simulated verification result');
  const sessionId = "sess_mock_" + Math.random().toString(36).substring(2, 10);

  // Default mock response for development - always returns APPROVE
  // Use ActiveCall simulation buttons to test other outcomes
  return {
    request_id: requestId,
    decision: "APPROVE",
    reason_public: "OK",
    risk_level: "LOW",
    session_id: sessionId,
    api_version: "v1",
    timestamp: new Date().toISOString(),
    _mock: true,
    _warning: "MOCK MODE - Use simulation buttons to test all 5 outcomes"
  };
}

/**
 * Submit transcript segments to AAA-VR for vishing and social engineering risk analysis.
 * Calls POST /v1/risk/transcript
 * 
 * Complies with frozen AAA-VR contract (CALLGUARD_RISK_INTEGRATION_REPORT.md):
 * - request_id, session_id, risk_level (LOW, MEDIUM, HIGH, CRITICAL)
 * - risk_indicators (array of public reason codes)
 * - recommended_action (APPROVE, REVIEW, STEP_UP, DENY)
 * - confidence (float between 0.0 and 1.0)
 * - model_version ("aaa-vr-transcript-risk-v1")
 * - analyzed_at (ISO 8601 string)
 * 
 * @param {Array<{speaker: string, text: string, timestamp: string}> | string} segments
 * @param {string} [sessionId]
 * @param {string} [authToken]
 */
export async function analyzeTranscriptRisk(segments, sessionId = "call-session-demo", authToken = null) {
  if (USE_MOCK) {
    let textToAnalyze = "";
    if (Array.isArray(segments)) {
      textToAnalyze = segments.map(s => (s && s.text ? s.text : "")).join(" ").toLowerCase();
    } else if (typeof segments === "string") {
      textToAnalyze = segments.toLowerCase();
    }
    
    const nowIso = new Date().toISOString();
    const requestId = "req_" + Math.random().toString(36).substring(2, 10) + "-" + Math.random().toString(36).substring(2, 6);
    const resolvedSessionId = sessionId || "call-session-demo";

    // Hard negative check: Genuine security advisory from bank agent
    const isSecurityAdvisory = textToAnalyze.includes("never share your otp") || 
      textToAnalyze.includes("never ask you to share") ||
      textToAnalyze.includes("fraud prevention unit");

    if (isSecurityAdvisory) {
      return {
        request_id: requestId,
        session_id: resolvedSessionId,
        risk_level: "LOW",
        risk_indicators: [],
        recommended_action: "APPROVE",
        confidence: 0.98,
        model_version: "aaa-vr-transcript-risk-v1",
        analyzed_at: nowIso,
        // Backward-compatibility aliases
        reason_public: "ROUTINE_INQUIRY",
        detected_triggers: [],
        timestamp: nowIso,
        _mock: true
      };
    }

    // 1. Critical threat: Credential harvesting, extortion, termination threats, OTP bypass
    const hasCredentialHarvesting = textToAnalyze.includes("bypass") || 
      (textToAnalyze.includes("otp") && (textToAnalyze.includes("read back") || textToAnalyze.includes("immediately") || textToAnalyze.includes("share"))) ||
      (textToAnalyze.includes("password") && textToAnalyze.includes("give")) ||
      (textToAnalyze.includes("pin") && textToAnalyze.includes("tell"));
    const hasPressureTactics = textToAnalyze.includes("terminate") || 
      (textToAnalyze.includes("supervisor") && textToAnalyze.includes("fire")) ||
      textToAnalyze.includes("arrest") || textToAnalyze.includes("legal action") ||
      textToAnalyze.includes("no time for procedures");
    const hasImpersonation = textToAnalyze.includes("director of") || 
      textToAnalyze.includes("federal agent") || 
      (textToAnalyze.includes("fraud desk") && textToAnalyze.includes("calling from"));

    if (hasCredentialHarvesting || (hasPressureTactics && hasImpersonation)) {
      const indicators = [];
      if (hasCredentialHarvesting) indicators.push("CREDENTIAL_HARVESTING_ATTEMPT");
      if (hasPressureTactics) indicators.push("PRESSURE_TACTICS_DETECTED");
      if (hasImpersonation) indicators.push("IMPERSONATION_ATTEMPT");
      if (indicators.length === 0) indicators.push("CREDENTIAL_HARVESTING_ATTEMPT");

      return {
        request_id: requestId,
        session_id: resolvedSessionId,
        risk_level: "CRITICAL",
        risk_indicators: indicators,
        recommended_action: "DENY",
        confidence: 0.96,
        model_version: "aaa-vr-transcript-risk-v1",
        analyzed_at: nowIso,
        // Backward-compatibility aliases
        reason_public: indicators[0],
        detected_triggers: indicators,
        timestamp: nowIso,
        _mock: true
      };
    }

    // 2. High risk: Urgent wire / funds transfer demands with pressure or unverified destination
    const hasUrgentTransfer = (textToAnalyze.includes("urgent") || textToAnalyze.includes("immediately")) && 
      (textToAnalyze.includes("wire") || textToAnalyze.includes("transfer") || textToAnalyze.includes("funds"));
    
    if (hasUrgentTransfer || hasPressureTactics) {
      const indicators = [];
      if (hasUrgentTransfer) indicators.push("URGENT_TRANSFER_REQUEST");
      if (hasPressureTactics) indicators.push("PRESSURE_TACTICS_DETECTED");
      if (textToAnalyze.includes("account ending") || textToAnalyze.includes("account number") || textToAnalyze.includes("routing number")) {
        indicators.push("ACCOUNT_NUMBER_MENTIONED");
      }
      if (indicators.length === 0) indicators.push("URGENT_TRANSFER_REQUEST");

      return {
        request_id: requestId,
        session_id: resolvedSessionId,
        risk_level: "HIGH",
        risk_indicators: indicators,
        recommended_action: "STEP_UP",
        confidence: 0.89,
        model_version: "aaa-vr-transcript-risk-v1",
        analyzed_at: nowIso,
        // Backward-compatibility aliases
        reason_public: indicators[0],
        detected_triggers: indicators,
        timestamp: nowIso,
        _mock: true
      };
    }

    // 3. Medium risk: Address change request, unverified beneficiary, sensitive account disclosure
    const hasAddressChange = textToAnalyze.includes("address") || textToAnalyze.includes("unverified beneficiary") || textToAnalyze.includes("new beneficiary");
    const hasAccountMention = textToAnalyze.includes("account number") || textToAnalyze.includes("routing") || textToAnalyze.includes("iban");

    if (hasAddressChange || hasAccountMention) {
      const indicators = [];
      if (hasAddressChange) indicators.push("UNVERIFIED_BENEFICIARY");
      if (hasAccountMention) indicators.push("ACCOUNT_NUMBER_MENTIONED");

      return {
        request_id: requestId,
        session_id: resolvedSessionId,
        risk_level: "MEDIUM",
        risk_indicators: indicators,
        recommended_action: "REVIEW",
        confidence: 0.74,
        model_version: "aaa-vr-transcript-risk-v1",
        analyzed_at: nowIso,
        // Backward-compatibility aliases
        reason_public: indicators[0],
        detected_triggers: indicators,
        timestamp: nowIso,
        _mock: true
      };
    }

    // 4. Low risk default: Routine balance inquiry, standard transaction checks
    return {
      request_id: requestId,
      session_id: resolvedSessionId,
      risk_level: "LOW",
      risk_indicators: [],
      recommended_action: "APPROVE",
      confidence: 0.95,
      model_version: "aaa-vr-transcript-risk-v1",
      analyzed_at: nowIso,
      // Backward-compatibility aliases
      reason_public: "ROUTINE_INQUIRY",
      detected_triggers: [],
      timestamp: nowIso,
      _mock: true
    };
  }

  // Live backend proxy call (Aligned with TranscriptRiskRequest schema in backend/app/schemas/risk.py)
  let transcriptText = "";
  if (Array.isArray(segments)) {
    transcriptText = segments
      .map(s => (s && s.text ? s.text : ""))
      .filter(Boolean)
      .join(" ");
  } else if (typeof segments === "string") {
    transcriptText = segments;
  }
  if (!transcriptText.trim()) {
    transcriptText = "No speech transcript available";
  }

  const headers = {
    "Content-Type": "application/json",
    "X-Request-ID": `cg-${Date.now()}`
  };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  const res = await fetch(`${API_BASE}/v1/risk/transcript`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      session_id: sessionId || "call-session-demo",
      transcript: transcriptText,
      context: {
        client: "callguard-console",
        version: "0.1.0"
      }
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
