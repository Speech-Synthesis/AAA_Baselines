import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createChallenge, verifyVoice } from '../services/api.js'
import RiskPanel from '../components/RiskPanel.jsx'

/**
 * Banking Shield Voice Verification Page
 *
 * Voice authentication for high-risk actions.
 * Uses AAA-controlled capture component.
 */

function Verification({ user, onLogout }) {
  const navigate = useNavigate()
  const [step, setStep] = useState('challenge') // challenge, recording, result
  const [challenge, setChallenge] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [countdown, setCountdown] = useState(90)
  const [pendingTransfer, setPendingTransfer] = useState(null)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)
  const countdownRef = useRef(null)

  // Load pending transfer context
  useEffect(() => {
    const transfer = sessionStorage.getItem('pendingTransfer')
    if (transfer) {
      setPendingTransfer(JSON.parse(transfer))
    }
  }, [])

  // Initialize challenge
  useEffect(() => {
    async function initChallenge() {
      setLoading(true)
      try {
        const ch = await createChallenge(
          user.userRef,
          pendingTransfer ? 'high_risk_transaction' : 'standard_verification'
        )
        setChallenge(ch)
        startCountdown(ch.ttl_seconds || 90)
      } catch (err) {
        setError('Failed to create challenge: ' + err.message)
      }
      setLoading(false)
    }
    initChallenge()

    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [user.userRef])

  const startCountdown = (seconds) => {
    setCountdown(seconds)
    countdownRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownRef.current)
          setError('Challenge expired. Please try again.')
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }

  const startRecording = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await submitVerification(audioBlob)
      }

      mediaRecorder.start()
      setIsRecording(true)
      setStep('recording')

      // Auto-stop after 6 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          stopRecording()
        }
      }, 6000)
    } catch (err) {
      setError('Microphone access denied. Please allow microphone access.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
  }

  const submitVerification = async (audioBlob) => {
    setLoading(true)
    if (countdownRef.current) {
      clearInterval(countdownRef.current)
    }

    try {
      const verifyResult = await verifyVoice(
        user.userRef,
        challenge.challenge_id || challenge.token,
        audioBlob
      )

      setResult(verifyResult)
      setStep('result')

      // If approved and there's a pending transfer, complete it
      if (verifyResult.decision === 'APPROVE' && pendingTransfer) {
        sessionStorage.removeItem('pendingTransfer')
      }
    } catch (err) {
      setError('Verification failed: ' + err.message)
      setResult({
        decision: 'DENY',
        reason: err.message,
        risk_level: 'HIGH'
      })
      setStep('result')
    }
    setLoading(false)
  }

  const handleRetry = async () => {
    setStep('challenge')
    setResult(null)
    setError('')
    setLoading(true)
    try {
      const ch = await createChallenge(user.userRef, 'standard_verification')
      setChallenge(ch)
      startCountdown(ch.ttl_seconds || 90)
    } catch (err) {
      setError('Failed to create new challenge: ' + err.message)
    }
    setLoading(false)
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

        {(step === 'challenge' || step === 'recording') && (
          <div className="card verification-card">
            <div className="countdown-display">
              <span className={countdown < 30 ? 'warning' : ''}>
                Time remaining: {countdown}s
              </span>
            </div>

            <div className="challenge-display">
              <h2>Please say:</h2>
              <div className="challenge-phrase">
                "{challenge?.phrase || 'Loading...'}"
              </div>
            </div>

            <div className="recording-controls">
              {isRecording ? (
                <div className="recording-active">
                  <div className="recording-indicator">
                    <span className="pulse"></span>
                    Recording...
                  </div>
                  <button className="btn-stop" onClick={stopRecording}>
                    Stop Recording
                  </button>
                </div>
              ) : loading ? (
                <div className="processing">Processing...</div>
              ) : (
                <button
                  className="btn-record large"
                  onClick={startRecording}
                  disabled={!challenge || countdown === 0}
                >
                  &#x1F3A4; Start Recording
                </button>
              )}
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="verification-info">
              <p>
                Speak the phrase above clearly. Your voice will be verified against
                your enrolled voiceprint.
              </p>
            </div>
          </div>
        )}

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
    </div>
  )
}

export default Verification
