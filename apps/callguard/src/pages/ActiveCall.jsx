import React, { useState, useEffect, useRef } from 'react';
import RiskPanel from '../components/RiskPanel';
import EscalationPanel from '../components/EscalationPanel';
import AuditHistory from '../components/AuditHistory';
import { createChallenge, createCaptureGrant, getAPIBaseURL, analyzeTranscriptRisk } from '../services/api';

/**
 * ActiveCall Page
 *
 * Interactive Console for managing an in-flight simulated call.
 * Integrates AAA phrase challenge workflow and AAA-VR vishing defense.
 *
 * ARCHITECTURE (per HOST_APPS.md):
 * - CallGuard NEVER handles raw audio directly
 * - AAA-controlled capture component records and uploads audio directly to AAA
 * - Host app embeds the capture component via iframe when real verification needed
 * - Simulation buttons provided for demo purposes
 */
export default function ActiveCall({ call, onBackToDashboard, onUpdateCall, onAddAuditLog, allAuditLogs }) {
  const [elapsed, setElapsed] = useState(call.duration || 60);
  const [challengeSession, setChallengeSession] = useState(null);
  const [captureGrant, setCaptureGrant] = useState(null);
  const [isRequestingChallenge, setIsRequestingChallenge] = useState(false);
  const [verificationOutcome, setVerificationOutcome] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [isAnalyzingRisk, setIsAnalyzingRisk] = useState(false);
  const [showCaptureModal, setShowCaptureModal] = useState(false);
  const [captureStatus, setCaptureStatus] = useState('');

  const iframeRef = useRef(null);
  const API_BASE = getAPIBaseURL();

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

  // Listen for messages from AAA capture component
  useEffect(() => {
    function handleCaptureMessage(event) {
      const data = event.data;
      if (!data || data.source !== 'aaa-capture') return;

      switch (data.type) {
        case 'ready':
          setCaptureStatus('Ready - Ask customer to speak the phrase');
          break;

        case 'recording_started':
          setCaptureStatus('Recording customer voice...');
          break;

        case 'recording_stopped':
          setCaptureStatus('Processing verification...');
          break;

        case 'verification_complete':
          // AAA completed verification - we only get safe info
          const outcome = {
            decision: data.decision,
            risk_level: data.risk_level,
            reason_public: data.reason_public,
            requestId: data.session_id,
            details: getOutcomeDetails(data.decision),
            requires_fresh_challenge: data.requires_fresh_challenge,
            requires_human_review: data.requires_human_review
          };

          setVerificationOutcome(outcome);
          setChallengeSession(null);
          setCaptureGrant(null);
          setShowCaptureModal(false);
          setCaptureStatus('');

          // Record in audit log
          onAddAuditLog({
            id: "AUD-" + Math.floor(Math.random() * 9000 + 1000),
            timestamp: new Date().toISOString(),
            requestId: data.session_id,
            customerRef: call.customerRef,
            tenantId: "callcentre_demo",
            decision: data.decision,
            riskLevel: data.risk_level,
            reasonPublic: data.reason_public,
            actionTaken: `Voice verification ${data.decision}`
          });
          break;

        case 'expired':
          setCaptureStatus('Session expired');
          setShowCaptureModal(false);
          break;

        case 'error':
          setCaptureStatus(`Error: ${data.error}`);
          break;

        default:
          break;
      }
    }

    window.addEventListener('message', handleCaptureMessage);
    return () => window.removeEventListener('message', handleCaptureMessage);
  }, [call.customerRef, onAddAuditLog]);

  const getOutcomeDetails = (decision) => {
    const details = {
      APPROVE: "Exact phrase matched deterministically (OK). Speaker biometric confirmed.",
      DENY: "Spoken phrase mismatch or speaker verification failed.",
      STEP_UP: "Additional verification required. Please request a fresh challenge.",
      REVIEW: "Human review required. Transaction hold applied pending supervisor approval.",
      UNAVAILABLE: "Authentication service temporarily unavailable. Please try again later."
    };
    return details[decision] || "Unknown outcome.";
  };

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
      // Step 1: Create challenge
      const session = await createChallenge(call.customerRef, "callguard_high_risk_verification");
      setChallengeSession(session);

      // Step 2: Create capture grant for AAA-controlled recording
      const grant = await createCaptureGrant(call.customerRef, session.challenge_id || session.token);
      setCaptureGrant(grant);
    } catch (err) {
      alert("Failed to create challenge: " + err.message);
    } finally {
      setIsRequestingChallenge(false);
    }
  };

  const handleLaunchCapture = () => {
    setShowCaptureModal(true);
    setCaptureStatus('Initializing secure capture...');
  };

  /**
   * Simulate customer voice verification response (for demo purposes only).
   * In production, real verification goes through AAA capture component.
   */
  const handleSimulateCustomerResponse = (outcomeType = 'APPROVE') => {
    const requestId = "req_" + Math.random().toString(36).substring(2, 10);

    const outcomes = {
      APPROVE: {
        decision: "APPROVE",
        risk_level: "LOW",
        reason_public: "OK",
        details: "Exact phrase matched deterministically (OK). Speaker biometric confirmed."
      },
      DENY: {
        decision: "DENY",
        risk_level: "HIGH",
        reason_public: "AUTH_FAILED",
        details: "Spoken phrase mismatch or speaker verification failed."
      },
      STEP_UP: {
        decision: "STEP_UP",
        risk_level: "LOW",
        reason_public: "TRY_AGAIN",
        details: "Additional verification required. Please request a fresh challenge.",
        requires_fresh_challenge: true
      },
      REVIEW: {
        decision: "REVIEW",
        risk_level: "HIGH",
        reason_public: "REVIEW_REQUIRED",
        details: "Human review required. Transaction hold applied pending supervisor approval.",
        requires_human_review: true
      },
      UNAVAILABLE: {
        decision: "UNAVAILABLE",
        risk_level: "MEDIUM",
        reason_public: "SERVICE_UNAVAILABLE",
        details: "Authentication service temporarily unavailable. Please try again later."
      }
    };

    const outcome = { ...outcomes[outcomeType], requestId };

    setVerificationOutcome(outcome);
    setChallengeSession(null);
    setCaptureGrant(null);

    // Record in audit log
    const actionMessages = {
      APPROVE: "Voice verification APPROVED (simulated)",
      DENY: "Voice verification DENIED (simulated)",
      STEP_UP: "Voice verification STEP_UP (simulated)",
      REVIEW: "Voice verification REVIEW (simulated)",
      UNAVAILABLE: "Voice verification UNAVAILABLE (simulated)"
    };

    onAddAuditLog({
      id: "AUD-" + Math.floor(Math.random() * 9000 + 1000),
      timestamp: new Date().toISOString(),
      requestId,
      customerRef: call.customerRef,
      tenantId: "callcentre_demo",
      decision: outcome.decision,
      riskLevel: outcome.risk_level,
      reasonPublic: outcome.reason_public,
      actionTaken: actionMessages[outcomeType]
    });
  };

  const getCaptureURL = () => {
    if (!captureGrant) return '';
    return `${API_BASE}${captureGrant.capture_url}`;
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${rem.toString().padStart(2, '0')}`;
  };

  const callLogs = allAuditLogs.filter(l => l.customerRef === call.customerRef);

  return (
    <div className="container">
      {/* AAA Capture Modal */}
      {showCaptureModal && captureGrant && (
        <div className="capture-modal-overlay">
          <div className="capture-modal">
            <div className="capture-modal-header">
              <h3>AAA Secure Voice Capture</h3>
              <button className="close-btn" onClick={() => setShowCaptureModal(false)}>&times;</button>
            </div>
            <div className="capture-modal-body">
              <p className="capture-instruction">
                Direct the customer to speak the challenge phrase into their device.
                Audio is captured securely by AAA - never through CallGuard.
              </p>
              {captureStatus && <p className="capture-status">{captureStatus}</p>}
              <div className="aaa-capture-container">
                <iframe
                  ref={iframeRef}
                  src={getCaptureURL()}
                  title="AAA Voice Capture"
                  className="aaa-capture-iframe"
                  allow="microphone"
                  sandbox="allow-scripts allow-same-origin allow-forms"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Navigation */}
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button className="btn btn-secondary" onClick={onBackToDashboard}>
          &larr; Return to Call Queue
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
                  &#x1F512; <strong>Direct Upload Guardrail:</strong> AAA capture component streams audio straight to AAA. CallGuard never proxies raw audio.
                </div>

                {/* AAA Capture Launch Button */}
                {captureGrant && (
                  <div style={{ marginBottom: '12px' }}>
                    <button
                      className="btn btn-primary"
                      onClick={handleLaunchCapture}
                      style={{ background: '#059669', width: '100%' }}
                    >
                      &#x1F3A4; Launch AAA Capture Component (Real Verification)
                    </button>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px', textAlign: 'center' }}>
                      Opens secure AAA capture for customer voice recording
                    </p>
                  </div>
                )}

                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px', marginTop: '8px' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    <strong>Demo Simulation:</strong> Use buttons below to simulate verification outcomes
                  </p>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleSimulateCustomerResponse('APPROVE')}
                    >
                      &#x2713; APPROVE
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleSimulateCustomerResponse('DENY')}
                    >
                      &#x2717; DENY
                    </button>
                    <button
                      className="btn btn-sm"
                      style={{ background: '#f97316', color: 'white' }}
                      onClick={() => handleSimulateCustomerResponse('STEP_UP')}
                    >
                      &#x21BB; STEP_UP
                    </button>
                    <button
                      className="btn btn-sm"
                      style={{ background: '#eab308', color: 'black' }}
                      onClick={() => handleSimulateCustomerResponse('REVIEW')}
                    >
                      &#x1F441; REVIEW
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleSimulateCustomerResponse('UNAVAILABLE')}
                    >
                      &#x26A0; UNAVAILABLE
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Verification Outcome Display - All 5 Decision Types */}
            {verificationOutcome && (
              <div style={{
                marginTop: '16px',
                padding: '16px',
                borderRadius: '8px',
                background: {
                  APPROVE: 'rgba(16, 185, 129, 0.1)',
                  DENY: 'rgba(239, 68, 68, 0.1)',
                  STEP_UP: 'rgba(249, 115, 22, 0.1)',
                  REVIEW: 'rgba(234, 179, 8, 0.1)',
                  UNAVAILABLE: 'rgba(148, 163, 184, 0.1)'
                }[verificationOutcome.decision] || 'rgba(148, 163, 184, 0.1)',
                border: `1px solid ${
                  {
                    APPROVE: 'var(--risk-low)',
                    DENY: 'var(--risk-high)',
                    STEP_UP: '#f97316',
                    REVIEW: '#eab308',
                    UNAVAILABLE: 'var(--text-muted)'
                  }[verificationOutcome.decision] || 'var(--border)'
                }`
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{
                    fontWeight: 'bold',
                    fontSize: '1rem',
                    color: {
                      APPROVE: 'var(--risk-low)',
                      DENY: 'var(--risk-high)',
                      STEP_UP: '#f97316',
                      REVIEW: '#eab308',
                      UNAVAILABLE: 'var(--text-muted)'
                    }[verificationOutcome.decision] || 'var(--text-main)'
                  }}>
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
                {verificationOutcome.requires_fresh_challenge && (
                  <div style={{ fontSize: '0.8rem', color: '#f97316', marginTop: '6px', fontStyle: 'italic' }}>
                    &#x21BB; A fresh challenge is required. Click "Initiate Customer Voice Verification" to retry.
                  </div>
                )}
                {verificationOutcome.requires_human_review && (
                  <div style={{ fontSize: '0.8rem', color: '#eab308', marginTop: '6px', fontStyle: 'italic' }}>
                    &#x1F441; Human review pending. Supervisor will be notified.
                  </div>
                )}
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

      {/* Styles for capture modal */}
      <style>{`
        .capture-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .capture-modal {
          background: var(--bg-card, #1e293b);
          border-radius: 12px;
          width: 90%;
          max-width: 500px;
          max-height: 90vh;
          overflow: hidden;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        .capture-modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border, #334155);
        }

        .capture-modal-header h3 {
          margin: 0;
          color: var(--text-main, #f1f5f9);
        }

        .close-btn {
          background: none;
          border: none;
          color: var(--text-muted, #94a3b8);
          font-size: 24px;
          cursor: pointer;
          padding: 0 8px;
        }

        .close-btn:hover {
          color: var(--text-main, #f1f5f9);
        }

        .capture-modal-body {
          padding: 20px;
        }

        .capture-instruction {
          font-size: 0.9rem;
          color: var(--text-muted, #94a3b8);
          margin-bottom: 12px;
        }

        .capture-status {
          color: #3b82f6;
          font-weight: 500;
          margin-bottom: 12px;
          text-align: center;
        }

        .aaa-capture-container {
          border: 1px solid var(--border, #334155);
          border-radius: 8px;
          overflow: hidden;
          background: #f8fafc;
        }

        .aaa-capture-iframe {
          width: 100%;
          height: 450px;
          border: none;
        }
      `}</style>
    </div>
  );
}
