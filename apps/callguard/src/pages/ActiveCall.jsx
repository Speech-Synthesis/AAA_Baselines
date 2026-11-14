import React, { useState, useEffect } from 'react';
import RiskPanel from '../components/RiskPanel';
import EscalationPanel from '../components/EscalationPanel';
import AuditHistory from '../components/AuditHistory';
import { createChallenge, analyzeTranscriptRisk } from '../services/api';

/**
 * ActiveCall Page
 * 
 * Interactive Console for managing an in-flight simulated call.
 * Integrates AAA phrase challenge workflow and AAA-VR vishing defense.
 */
export default function ActiveCall({ call, onBackToDashboard, onUpdateCall, onAddAuditLog, allAuditLogs }) {
  const [elapsed, setElapsed] = useState(call.duration || 60);
  const [challengeSession, setChallengeSession] = useState(null);
  const [isRequestingChallenge, setIsRequestingChallenge] = useState(false);
  const [verificationOutcome, setVerificationOutcome] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [isAnalyzingRisk, setIsAnalyzingRisk] = useState(false);

  // Timer simulation
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Initial risk assessment from transcript
  useEffect(() => {
    handleRunRiskAnalysis();
  }, [call.id]);

  const handleRunRiskAnalysis = async () => {
    setIsAnalyzingRisk(true);
    try {
      const res = await analyzeTranscriptRisk(call.transcript);
      setRiskData(res);
    } catch (err) {
      console.error("Risk analysis error:", err);
    } finally {
      setIsAnalyzingRisk(false);
    }
  };

  const handleInitiateVerification = async () => {
    setIsRequestingChallenge(true);
    setVerificationOutcome(null);
    try {
      // Calls POST /v1/challenges
      const session = await createChallenge(call.customerRef, "callguard_high_risk_verification");
      setChallengeSession(session);
    } catch (err) {
      alert("Failed to create challenge: " + err.message);
    } finally {
      setIsRequestingChallenge(false);
    }
  };

  const handleSimulateCustomerResponse = (success = true) => {
    // In approved AAA architecture:
    // User speaks phrase into AAA-controlled capture component.
    // Component uploads directly to AAA POST /v1/verify.
    // Host backend queries final safe decision.
    const requestId = "req_" + Math.random().toString(36).substring(2, 10);
    const outcome = success ? {
      decision: "APPROVE",
      risk_level: "LOW",
      reason_public: "REQUIRED_CHECKS_PASSED",
      details: "Exact phrase matched deterministically (OK). Speaker biometric confirmed.",
      requestId
    } : {
      decision: "DENY",
      risk_level: "HIGH",
      reason_public: "CHALLENGE_MISMATCH",
      details: "Spoken phrase mismatch or near-miss detected by AAA-ASR verifier.",
      requestId
    };

    setVerificationOutcome(outcome);
    setChallengeSession(null);

    // Record in audit log
    onAddAuditLog({
      id: "AUD-" + Math.floor(Math.random() * 9000 + 1000),
      timestamp: new Date().toISOString(),
      requestId,
      customerRef: call.customerRef,
      tenantId: "callcentre_demo",
      decision: outcome.decision,
      riskLevel: outcome.risk_level,
      reasonPublic: outcome.reason_public,
      actionTaken: success ? "Voice verification APPROVED" : "Voice verification DENIED - Prompt Escalation"
    });
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  const callLogs = allAuditLogs.filter(l => l.customerRef === call.customerRef);

  return (
    <div className="container">
      {/* Top Navigation */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn btn-secondary" onClick={onBackToDashboard}>
          ← Return to Call Queue
        </button>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="badge badge-blue">CHANNEL: {call.channel}</span>
          <span className="badge badge-low">STATUS: {call.status}</span>
        </div>
      </div>

      {/* Meta Bar */}
      <div className="call-meta-bar">
        <div className="meta-item">
          <span className="meta-label">Active Session ID</span>
          <span className="meta-value" style={{ fontFamily: 'monospace' }}>{call.id}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Customer Pseudonym Ref</span>
          <span className="meta-value">{call.customerRef}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Call Duration</span>
          <span className="meta-value" style={{ color: 'var(--accent-cyan)' }}>{formatTime(elapsed)}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Demo Scenario</span>
          <span className="meta-value" style={{ fontSize: '0.85rem' }}>{call.scenarioName.split(':')[0]}</span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="active-call-grid">
        {/* Left Column: Transcript Stream & Voice Verification Box */}
        <div>
          {/* Transcript Panel */}
          <div className="card">
            <div className="card-title">
              <span>Live Synthetic Call Transcript</span>
              <span className="badge badge-blue">Seeded Stream</span>
            </div>

            <div className="transcript-box">
              {call.transcript.map(seg => (
                <div 
                  key={seg.id} 
                  className={`message-bubble ${seg.speaker === 'agent' ? 'bubble-agent' : 'bubble-caller'}`}
                >
                  <div className="bubble-header">
                    <strong>{seg.speaker === 'agent' ? 'Agent (Operator)' : 'Caller (Client)'}</strong>
                    <span>{seg.timestamp}</span>
                  </div>
                  <div className="bubble-text">{seg.text}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Voice Challenge Authentication Workflow */}
          <div className="card" style={{ marginTop: '20px' }}>
            <div className="card-title">
              <span>AAA Challenge Authentication (Exact Phrase Verification)</span>
              <span className="badge badge-blue">Tenant: callcentre_demo</span>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
              High-value operations require step-up biometric verification. AAA generates a single-use 
              unpredictable phrase (TTL: 90s). The customer speaks into the AAA-controlled capture component, 
              which uploads directly to AAA for exact-match phrase verification.
            </p>

            {!challengeSession && !verificationOutcome && (
              <button 
                className="btn btn-primary"
                onClick={handleInitiateVerification}
                disabled={isRequestingChallenge}
              >
                {isRequestingChallenge ? 'Requesting AAA Challenge...' : 'Initiate Customer Voice Verification'}
              </button>
            )}

            {/* Active Challenge Box */}
            {challengeSession && (
              <div className="challenge-box">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Challenge ID: <code>{challengeSession.challenge_id}</code> (TTL: {challengeSession.ttl_seconds}s)
                  </span>
                  <span className="badge badge-medium">Awaiting Audio Response</span>
                </div>

                <div className="challenge-phrase-display">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    PROMPT DISPLAYED TO CALLER ON SECURE COMPONENT:
                  </div>
                  <div className="phrase-text">"{challengeSession.phrase}"</div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  🔒 <strong>Direct Upload Guardrail:</strong> AAA capture component streams audio straight to <code>{challengeSession.capture.upload_url}</code> using short-lived capture grant. CallGuard never proxies raw audio.
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    className="btn btn-primary btn-sm"
                    onClick={() => handleSimulateCustomerResponse(true)}
                  >
                    Simulate: Caller Speaks Exact Phrase (OK)
                  </button>
                  <button 
                    className="btn btn-danger btn-sm"
                    onClick={() => handleSimulateCustomerResponse(false)}
                  >
                    Simulate: Caller Speaks Near-Miss / Wrong Phrase (DENIED)
                  </button>
                </div>
              </div>
            )}

            {/* Verification Outcome Display */}
            {verificationOutcome && (
              <div style={{ 
                marginTop: '16px', 
                padding: '16px', 
                borderRadius: '8px',
                background: verificationOutcome.decision === 'APPROVE' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                border: `1px solid ${verificationOutcome.decision === 'APPROVE' ? 'var(--risk-low)' : 'var(--risk-high)'}`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem', color: verificationOutcome.decision === 'APPROVE' ? 'var(--risk-low)' : 'var(--risk-high)' }}>
                    DECISION: {verificationOutcome.decision}
                  </div>
                  <span className="badge badge-blue">Req: {verificationOutcome.requestId}</span>
                </div>
                <div style={{ fontSize: '0.85rem' }}>
                  <strong>Public Reason:</strong> {verificationOutcome.reason_public}
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {verificationOutcome.details}
                </div>
                <button 
                  className="btn btn-secondary btn-sm" 
                  style={{ marginTop: '12px' }}
                  onClick={() => setVerificationOutcome(null)}
                >
                  Clear & Re-test Verification
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Vishing Risk & Escalation Panels */}
        <div>
          <RiskPanel 
            riskData={riskData} 
            onReevaluate={handleRunRiskAnalysis}
            isAnalyzing={isAnalyzingRisk}
          />

          <EscalationPanel 
            callId={call.id}
            customerRef={call.customerRef}
            initialStatus={call.riskLevel === 'HIGH' ? 'ESCALATED_PENDING_SUPERVISOR' : 'NORMAL'}
          />

          <AuditHistory logs={callLogs} />
        </div>
      </div>
    </div>
  );
}
