import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createChallenge, enrollVoice } from '../services/api.js'

/**
 * Banking Shield Voice Enrollment Page
 *
 * AAA-controlled capture component for voice enrollment.
 * Requires multiple utterances and consent per HOST_APPS.md.
 */

const REQUIRED_SAMPLES = 3

function Enrollment({ user, onLogout }) {
  const navigate = useNavigate()
  const [step, setStep] = useState('consent') // consent, recording, complete
  const [currentSample, setCurrentSample] = useState(0)
  const [samples, setSamples] = useState([])
  const [challenge, setChallenge] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const handleConsent = async () => {
    setLoading(true)
    try {
      // Get first challenge phrase
      const ch = await createChallenge(user.userRef, 'voice_enrollment')
      setChallenge(ch)
      setStep('recording')
    } catch (err) {
      setError('Failed to start enrollment: ' + err.message)
    }
    setLoading(false)
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
        await handleRecordingComplete(audioBlob)
      }

      mediaRecorder.start()
      setIsRecording(true)

      // Auto-stop after 5 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          stopRecording()
        }
      }, 5000)
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

  const handleRecordingComplete = async (audioBlob) => {
    setLoading(true)
    try {
      // Store sample locally first
      const newSamples = [...samples, {
        blob: audioBlob,
        challenge: challenge,
        recordedAt: new Date().toISOString()
      }]
      setSamples(newSamples)

      if (newSamples.length < REQUIRED_SAMPLES) {
        // Get next challenge
        setCurrentSample(newSamples.length)
        const ch = await createChallenge(user.userRef, 'voice_enrollment')
        setChallenge(ch)
      } else {
        // All samples collected - submit enrollment
        await submitEnrollment(newSamples)
      }
    } catch (err) {
      setError('Failed to process recording: ' + err.message)
    }
    setLoading(false)
  }

  const submitEnrollment = async (allSamples) => {
    setLoading(true)
    try {
      // Submit all samples to AAA enrollment endpoint
      for (const sample of allSamples) {
        await enrollVoice(user.userRef, sample.blob)
      }
      setStep('complete')
    } catch (err) {
      setError('Enrollment failed: ' + err.message)
    }
    setLoading(false)
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
                  style={{ width: `${(currentSample / REQUIRED_SAMPLES) * 100}%` }}
                />
              </div>
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
                  <button
                    className="btn-stop"
                    onClick={stopRecording}
                  >
                    Stop Recording
                  </button>
                </div>
              ) : (
                <button
                  className="btn-record"
                  onClick={startRecording}
                  disabled={loading || !challenge}
                >
                  {loading ? 'Processing...' : '&#x1F3A4; Start Recording'}
                </button>
              )}
            </div>

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
            <Link to="/dashboard" className="btn-primary">
              Return to Dashboard
            </Link>
          </div>
        )}
      </main>
    </div>
  )
}

export default Enrollment
