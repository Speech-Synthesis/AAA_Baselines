import { useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

function App() {
  const [tab, setTab] = useState('register')
  const [userId, setUserId] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState(null)
  const [challenge, setChallenge] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState(null)

  const register = async () => {
    try {
      const res = await axios.post(`${API_BASE}/auth/register`, { name, email })
      setUserId(res.data.user_id)
      setStatus({ type: 'success', message: `Registered! User ID: ${res.data.user_id}` })
    } catch (err) {
      setStatus({ type: 'error', message: err.response?.data?.detail || 'Registration failed' })
    }
  }

  const startRecording = async (onStop) => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    const chunks = []

    recorder.ondataavailable = (e) => chunks.push(e.data)
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/wav' })
      stream.getTracks().forEach(t => t.stop())
      onStop(blob)
    }

    recorder.start()
    setMediaRecorder(recorder)
    setIsRecording(true)
  }

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop()
      setIsRecording(false)
    }
  }

  const enroll = async (audioBlob) => {
    const formData = new FormData()
    formData.append('user_id', userId)
    formData.append('audio', audioBlob, 'enrollment.wav')

    try {
      const res = await axios.post(`${API_BASE}/auth/enroll`, formData)
      setStatus({ type: 'success', message: `Enrolled! Sample count: ${res.data.sample_count}` })
    } catch (err) {
      setStatus({ type: 'error', message: err.response?.data?.detail || 'Enrollment failed' })
    }
  }

  const getChallenge = async () => {
    try {
      const res = await axios.get(`${API_BASE}/auth/challenge?user_id=${userId}`)
      setChallenge(res.data)
      setStatus({ type: 'success', message: 'Challenge received! Speak the phrase.' })
    } catch (err) {
      setStatus({ type: 'error', message: err.response?.data?.detail || 'Failed to get challenge' })
    }
  }

  const verify = async (audioBlob) => {
    if (!challenge) return

    const formData = new FormData()
    formData.append('user_id', userId)
    formData.append('token', challenge.token)
    formData.append('audio', audioBlob, 'verify.wav')

    try {
      const res = await axios.post(`${API_BASE}/auth/verify`, formData)
      const data = res.data
      setStatus({
        type: data.result === 'ACCEPT' ? 'success' : 'error',
        message: `${data.result}: ${data.reason}`,
        details: data
      })
      setChallenge(null)
    } catch (err) {
      setStatus({ type: 'error', message: err.response?.data?.detail || 'Verification failed' })
    }
  }

  return (
    <div className="container">
      <h1>AAA Engine</h1>
      <p style={{ textAlign: 'center', marginBottom: '1.5rem', opacity: 0.8 }}>
        Adaptive Audio Authentication
      </p>

      <div className="tabs">
        <button className={`tab ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>
          Register
        </button>
        <button className={`tab ${tab === 'enroll' ? 'active' : ''}`} onClick={() => setTab('enroll')}>
          Enroll
        </button>
        <button className={`tab ${tab === 'verify' ? 'active' : ''}`} onClick={() => setTab('verify')}>
          Verify
        </button>
      </div>

      {tab === 'register' && (
        <div className="card">
          <div className="form-group">
            <label>Name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="Enter your name" />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Enter your email" />
          </div>
          <button onClick={register}>Register</button>
        </div>
      )}

      {tab === 'enroll' && (
        <div className="card">
          <div className="form-group">
            <label>User ID</label>
            <input value={userId} onChange={e => setUserId(e.target.value)} placeholder="Enter user ID" />
          </div>
          <button
            className={isRecording ? 'recording' : ''}
            onClick={() => isRecording ? stopRecording() : startRecording(enroll)}
          >
            {isRecording ? 'Stop Recording' : 'Record Voice Sample (3+ seconds)'}
          </button>
        </div>
      )}

      {tab === 'verify' && (
        <div className="card">
          <div className="form-group">
            <label>User ID</label>
            <input value={userId} onChange={e => setUserId(e.target.value)} placeholder="Enter user ID" />
          </div>

          {!challenge ? (
            <button onClick={getChallenge}>Get Challenge</button>
          ) : (
            <>
              <div className="challenge-phrase">
                "{challenge.phrase}"
              </div>
              <button
                className={isRecording ? 'recording' : ''}
                onClick={() => isRecording ? stopRecording() : startRecording(verify)}
              >
                {isRecording ? 'Stop Recording' : 'Record Response'}
              </button>
            </>
          )}
        </div>
      )}

      {status && (
        <div className={`status ${status.type}`}>
          <strong>{status.message}</strong>
          {status.details && (
            <div className="result-details" style={{ marginTop: '0.5rem' }}>
              <div>L2: {status.details.l2_label} ({(status.details.l2_confidence * 100).toFixed(1)}%)</div>
              <div>L1 Score: {(status.details.l1_score * 100).toFixed(1)}%</div>
              {status.details.layer_blocked && <div>Blocked at Layer: {status.details.layer_blocked}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
