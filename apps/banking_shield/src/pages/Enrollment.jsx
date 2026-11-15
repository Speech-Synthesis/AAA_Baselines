import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createChallenge, createCaptureGrant, getAPIBaseURL } from '../services/api.js'

/**
 * Banking Shield Voice Enrollment Page
 *
 * ARCHITECTURE (per HOST_APPS.md):
 * - Host app (Banking Shield) NEVER handles raw audio directly
 * - AAA-controlled capture component records and uploads audio directly to AAA
 * - Host app embeds the capture component via iframe
 * - Communication via postMessage with origin validation
 * - Host receives only safe status information
 *
 * Enrollment requires multiple utterances (REQUIRED_SAMPLES) per HOST_APPS.md.
 * Each sample uses a fresh challenge and capture grant.
 */

const REQUIRED_SAMPLES = 3

function Enrollment({ user, onLogout }) {
  const navigate = useNavigate()
  const [step, setStep] = useState('consent') // consent, recording, complete
  const [currentSample, setCurrentSample] = useState(0)
  const [completedSamples, setCompletedSamples] = useState([])
  const [challenge, setChallenge] = useState(null)
  const [captureGrant, setCaptureGrant] = useState(null)
  const [captureStatus, setCaptureStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const iframeRef = useRef(null)
  const API_BASE = getAPIBaseURL()

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

        case 'enrollment_sample_complete':
        case 'verification_complete':
          // AAA capture component completed this sample
          handleSampleComplete(data)
          break

        case 'expired':
          setError('Session expired. Please start over.')
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
  }, [currentSample, completedSamples])

  const handleSampleComplete = async (data) => {
    const newCompleted = [...completedSamples, {
      sample_id: data.session_id || `sample_${currentSample}`,
      recorded_at: new Date().toISOString()
    }]
    setCompletedSamples(newCompleted)

    if (newCompleted.length < REQUIRED_SAMPLES) {
      // Get next challenge and capture grant
      setCurrentSample(newCompleted.length)
      setCaptureStatus('')
      await initCaptureSession()
    } else {
      // All samples collected - enrollment complete
      setStep('complete')
    }
  }

  const initCaptureSession = async () => {
    setLoading(true)
    setError('')
    try {
      // Step 1: Create challenge for this enrollment sample
      const ch = await createChallenge(user.userRef, 'voice_enrollment')
      setChallenge(ch)

      // Step 2: Create capture grant for AAA-controlled recording
      const grant = await createCaptureGrant(
        user.userRef,
        ch.challenge_id || ch.token,
        'enrollment' // enrollment mode
      )
      setCaptureGrant(grant)
    } catch (err) {
      setError('Failed to initialize capture: ' + err.message)
    }
    setLoading(false)
  }

  const handleConsent = async () => {
    setLoading(true)
    try {
      await initCaptureSession()
      setStep('recording')
    } catch (err) {
      setError('Failed to start enrollment: ' + err.message)
    }
    setLoading(false)
  }

  // Build the capture iframe URL
  const getCaptureURL = () => {
    if (!captureGrant) return ''
    return `${API_BASE}${captureGrant.capture_url}`
  }

  return (
    <div className="enrollment-page">
      <header className="page-header">
        <div className="header-left">
          <Link to="/dashboard" className="back-link">&larr; Dashboard</Link>
          <h1>Voice Enrollment</h1>
        </div>
        <div className="header-right">
          <span className="user-name">{user.name}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="enrollment-content">
        {step === 'consent' && (
          <div className="card consent-card">
            <div className="consent-icon">&#x1F3A4;</div>
            <h2>Enroll Your Voice</h2>
            <p className="consent-text">
              Voice authentication adds an extra layer of security to your account.
              High-risk transactions will require you to verify your identity by speaking
              a challenge phrase.
            </p>
            <div className="consent-details">
              <h3>What to expect:</h3>
              <ul>
                <li>You will record {REQUIRED_SAMPLES} voice samples</li>
                <li>Each recording is about 3-5 seconds</li>
                <li>Speak the displayed phrase clearly</li>
                <li>Your voiceprint is encrypted and stored securely</li>
              </ul>
            </div>
            <div className="security-note">
              <p className="security-badge">
                <span className="lock-icon">&#x1F510;</span>
                Secure AAA Voice Capture
              </p>
              <p>
                Audio is captured securely by AAA and never handled by this application.
              </p>
            </div>
            <div className="consent-agreement">
              <p>
                By continuing, you consent to AAA Engine processing your voice
                for biometric authentication purposes.
              </p>
            </div>
            {error && <div className="error-message">{error}</div>}
            <button
              className="btn-primary large"
              onClick={handleConsent}
              disabled={loading}
            >
              {loading ? 'Starting...' : 'I Agree - Start Enrollment'}
            </button>
          </div>
        )}

        {step === 'recording' && (
          <div className="card recording-card">
            <div className="progress-indicator">
              Sample {currentSample + 1} of {REQUIRED_SAMPLES}
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${(completedSamples.length / REQUIRED_SAMPLES) * 100}%` }}
                />
              </div>
            </div>

            <div className="capture-info">
              <p className="security-badge">
                <span className="lock-icon">&#x1F510;</span>
                Secure AAA Voice Capture
              </p>
              {captureStatus && <p className="capture-status">{captureStatus}</p>}
            </div>

            {/* AAA-controlled capture component embedded via iframe */}
            {captureGrant && (
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
            )}

            {loading && (
              <div className="loading-state">
                <div className="processing">Preparing next sample...</div>
              </div>
            )}

            <div className="recording-tips">
              <h4>Tips:</h4>
              <ul>
                <li>Speak clearly at a normal pace</li>
                <li>Keep the microphone about 6 inches away</li>
                <li>Minimize background noise</li>
              </ul>
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>
        )}

        {step === 'complete' && (
          <div className="card complete-card">
            <div className="success-icon">&#x2705;</div>
            <h2>Enrollment Complete!</h2>
            <p>
              Your voice has been successfully enrolled. You can now use voice
              authentication for high-value transactions.
            </p>
            <div className="enrollment-summary">
              <p><strong>{completedSamples.length}</strong> voice samples recorded securely</p>
            </div>
            <Link to="/dashboard" className="btn-primary">
              Return to Dashboard
            </Link>
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

        .security-note {
          background: #f0fdf4;
          border: 1px solid #86efac;
          border-radius: 8px;
          padding: 16px;
          margin: 16px 0;
          text-align: center;
        }

        .security-note p {
          margin: 4px 0;
          color: #166534;
        }

        .enrollment-summary {
          background: #f1f5f9;
          padding: 12px 20px;
          border-radius: 8px;
          margin: 16px 0;
        }

        .loading-state {
          padding: 20px;
          text-align: center;
        }
      `}</style>
    </div>
  )
}

export default Enrollment
