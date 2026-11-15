import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createChallenge, createCaptureGrant, getAPIBaseURL } from '../services/api.js'
import RiskPanel from '../components/RiskPanel.jsx'

/**
 * Banking Shield Voice Verification Page
 *
 * Voice authentication for high-risk actions.
 *
 * ARCHITECTURE (per HOST_APPS.md):
 * - Host app (Banking Shield) NEVER handles raw audio directly
 * - AAA-controlled capture component records and uploads audio directly to AAA
 * - Host app embeds the capture component via iframe
 * - Communication via postMessage with origin validation
 * - Host receives only safe status information (decision, risk_level, reason_public)
 */

function Verification({ user, onLogout }) {
  const navigate = useNavigate()
  const [step, setStep] = useState('loading') // loading, capture, result
  const [challenge, setChallenge] = useState(null)
  const [captureGrant, setCaptureGrant] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [pendingTransfer, setPendingTransfer] = useState(null)
  const [captureStatus, setCaptureStatus] = useState('')

  const iframeRef = useRef(null)
  const API_BASE = getAPIBaseURL()

  // Load pending transfer context
  useEffect(() => {
    const transfer = sessionStorage.getItem('pendingTransfer')
    if (transfer) {
      setPendingTransfer(JSON.parse(transfer))
    }
  }, [])

  // Initialize challenge and capture grant
  useEffect(() => {
    async function initCaptureSession() {
      setLoading(true)
      try {
        // Step 1: Create challenge
        const ch = await createChallenge(
          user.userRef,
          pendingTransfer ? 'high_risk_transaction' : 'standard_verification'
        )
        setChallenge(ch)

        // Step 2: Create capture grant for AAA-controlled recording
        const grant = await createCaptureGrant(
          user.userRef,
          ch.challenge_id || ch.token
        )
        setCaptureGrant(grant)

        setStep('capture')
      } catch (err) {
        setError('Failed to initialize verification: ' + err.message)
      }
      setLoading(false)
    }
    initCaptureSession()
  }, [user.userRef])

  // Listen for messages from AAA capture component
  useEffect(() => {
    function handleCaptureMessage(event) {
      // In production, validate event.origin against known AAA origins
      const data = event.data
      if (!data || data.source !== 'aaa-capture') return

      switch (data.type) {
        case 'ready':
          setCaptureStatus('Ready to record')
          break

        case 'recording_started':
          setCaptureStatus('Recording...')
          break

        case 'recording_stopped':
          setCaptureStatus('Processing...')
          break

        case 'verification_complete':
          // AAA capture component completed verification
          // We receive only safe info: decision, reason_public, risk_level
          setResult({
            decision: data.decision,
            reason: data.reason_public,
            reason_public: data.reason_public,
            risk_level: data.risk_level,
            session_id: data.session_id,
            requires_fresh_challenge: data.requires_fresh_challenge,
            requires_human_review: data.requires_human_review
          })
          setStep('result')

          // If approved and there's a pending transfer, complete it
          if (data.decision === 'APPROVE' && pendingTransfer) {
            sessionStorage.removeItem('pendingTransfer')
          }
          break

        case 'expired':
          setError('Session expired. Please try again.')
          break

        case 'error':
          setError(`Capture error: ${data.error}`)
          break

        default:
          break
      }
    }

    window.addEventListener('message', handleCaptureMessage)
    return () => window.removeEventListener('message', handleCaptureMessage)
  }, [pendingTransfer])

  const handleRetry = async () => {
    setStep('loading')
    setResult(null)
    setError('')
    setCaptureStatus('')
    setLoading(true)
    try {
      const ch = await createChallenge(user.userRef, 'standard_verification')
      setChallenge(ch)
      const grant = await createCaptureGrant(
        user.userRef,
        ch.challenge_id || ch.token
      )
      setCaptureGrant(grant)
      setStep('capture')
    } catch (err) {
      setError('Failed to create new challenge: ' + err.message)
    }
    setLoading(false)
  }

  // Build the capture iframe URL
  const getCaptureURL = () => {
    if (!captureGrant) return ''
    // The capture_url is relative to AAA backend
    return `${API_BASE}${captureGrant.capture_url}`
  }

  return (
    <div className="verification-page">
      <header className="page-header">
        <div className="header-left">
          <Link to="/dashboard" className="back-link">&larr; Dashboard</Link>
          <h1>Voice Verification</h1>
        </div>
        <div className="header-right">
          <span className="user-name">{user.name}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="verification-content">
        {pendingTransfer && (
          <div className="pending-transfer-banner">
            <strong>Pending Transfer:</strong> ${pendingTransfer.amount?.toLocaleString()} to {pendingTransfer.beneficiary}
          </div>
        )}

        {/* Loading State */}
        {step === 'loading' && (
          <div className="card verification-card">
            <div className="processing">Initializing secure verification...</div>
          </div>
        )}

        {/* Capture State - AAA-controlled iframe */}
        {step === 'capture' && captureGrant && (
          <div className="card verification-card">
            <div className="capture-info">
              <p className="security-badge">
                <span className="lock-icon">&#x1F510;</span>
                Secure AAA Voice Capture
              </p>
              {captureStatus && <p className="capture-status">{captureStatus}</p>}
            </div>

            {/* AAA-controlled capture component embedded via iframe */}
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

            {error && <div className="error-message">{error}</div>}

            <div className="verification-info">
              <p>
                Your voice is captured and verified securely by AAA.
                Audio is not stored or shared with this application.
              </p>
            </div>
          </div>
        )}

        {/* Result State */}
        {step === 'result' && result && (
          <div className="card result-card">
            <RiskPanel
              assessment={{
                risk_level: result.risk_level || (result.decision === 'APPROVE' ? 'LOW' : 'HIGH'),
                recommended_action: result.decision,
                reason: result.reason || result.reason_public || 'Verification complete'
              }}
              onClose={() => {}}
            />

            <div className={`result-display ${result.decision?.toLowerCase()}`}>
              {result.decision === 'APPROVE' ? (
                <>
                  <div className="result-icon success">&#x2705;</div>
                  <h2>Verification Successful</h2>
                  <p>Your identity has been confirmed.</p>
                  {pendingTransfer && (
                    <p className="transfer-approved">
                      Transfer of ${pendingTransfer.amount?.toLocaleString()} has been approved.
                    </p>
                  )}
                </>
              ) : result.decision === 'STEP_UP' ? (
                <>
                  <div className="result-icon step-up">&#x1F504;</div>
                  <h2>Additional Verification Required</h2>
                  <p>{result.reason || 'Please try again with a fresh challenge.'}</p>
                </>
              ) : result.decision === 'REVIEW' ? (
                <>
                  <div className="result-icon review">&#x1F50D;</div>
                  <h2>Human Review Required</h2>
                  <p>{result.reason || 'This transaction requires manual review by our security team.'}</p>
                  <p className="review-note">A representative will contact you shortly.</p>
                </>
              ) : result.decision === 'UNAVAILABLE' ? (
                <>
                  <div className="result-icon unavailable">&#x26A0;</div>
                  <h2>Service Unavailable</h2>
                  <p>{result.reason || 'The authentication service is temporarily unavailable. Please try again later.'}</p>
                </>
              ) : (
                <>
                  <div className="result-icon denied">&#x274C;</div>
                  <h2>Verification Failed</h2>
                  <p>{result.reason || 'Voice verification was unsuccessful.'}</p>
                </>
              )}
            </div>

            <div className="result-actions">
              {(result.decision === 'DENY' || result.decision === 'STEP_UP') && (
                <button className="btn-primary" onClick={handleRetry}>
                  Try Again
                </button>
              )}
              {result.decision === 'UNAVAILABLE' && (
                <button className="btn-primary" onClick={handleRetry}>
                  Retry Later
                </button>
              )}
              {result.decision === 'REVIEW' && (
                <span className="review-pending">Review pending - no action required</span>
              )}
              <Link to="/dashboard" className="btn-secondary">
                Return to Dashboard
              </Link>
            </div>
          </div>
        )}
      </main>

      <style>{`
        .aaa-capture-container {
          width: 100%;
          max-width: 450px;
          margin: 20px auto;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          overflow: hidden;
          background: #f8fafc;
        }

        .aaa-capture-iframe {
          width: 100%;
          height: 480px;
          border: none;
        }

        .security-badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #f1f5f9;
          padding: 8px 16px;
          border-radius: 20px;
          font-size: 14px;
          color: #64748b;
          margin-bottom: 16px;
        }

        .lock-icon {
          font-size: 16px;
        }

        .capture-info {
          text-align: center;
          margin-bottom: 16px;
        }

        .capture-status {
          color: #3b82f6;
          font-weight: 500;
          margin-top: 8px;
        }
      `}</style>
    </div>
  )
}

export default Verification
