import React, { useState, useEffect, useRef } from 'react';
import { getChallenge, verifyVoice } from '../api';

export function VerifyPage({ activeUser }) {
  const [challenge, setChallenge] = useState(null);
  const [loadingChallenge, setLoadingChallenge] = useState(false);
  const [timeLeft, setTimeLeft] = useState(90);
  const [isRecording, setIsRecording] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);
  const [forceSpoof, setForceSpoof] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Fetch challenge for active user
  const fetchNewChallenge = async () => {
    if (!activeUser) {
      setStatusMsg({ type: 'error', text: 'Please select an active user first!' });
      return;
    }

    setLoadingChallenge(true);
    setVerifyResult(null);
    setStatusMsg(null);
    setChallenge(null);
    clearInterval(timerRef.current);

    try {
      const data = await getChallenge(activeUser.id);
      setChallenge(data);
      setTimeLeft(90); // Reset 90s TTL timer

      // Start countdown
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setStatusMsg({ type: 'error', text: '⏱️ Challenge token expired (90s TTL reached). Request a new challenge.' });
            setChallenge(null);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to generate challenge phrase' });
    } finally {
      setLoadingChallenge(false);
    }
  };

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  const startRecording = async () => {
    if (!challenge) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleVerifySubmit(audioBlob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setStatusMsg(null);
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Microphone access denied' });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleVerifySubmit = async (audioBlob) => {
    setVerifying(true);
    clearInterval(timerRef.current);

    try {
      const res = await verifyVoice(activeUser.id, challenge.token, audioBlob, forceSpoof);
      setVerifyResult(res);
      setChallenge(null);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Verification endpoint failed' });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="glass-card">
      <div className="card-title">🔐 Adaptive Verification Protocol</div>
      <div className="card-subtitle">
        Dynamic Challenge-Response (Layer 3) → Deepfake Detection (Layer 2) → Speaker Verification (Layer 1)
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--warning)', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-md)' }}>
          ⚠️ No active user selected. Please go to the <strong>Register</strong> or <strong>Switch User</strong> tab.
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <div>
              Target Identity: <strong>{activeUser.name}</strong> ({activeUser.email})
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: forceSpoof ? 'var(--danger)' : 'var(--text-muted)' }}>
              <input
                type="checkbox"
                checked={forceSpoof}
                onChange={(e) => setForceSpoof(e.target.checked)}
              />
              Simulate Deepfake Attack (Test Layer 2)
            </label>
          </div>

          {!challenge ? (
            <button className="btn-primary" onClick={fetchNewChallenge} disabled={loadingChallenge}>
              {loadingChallenge ? 'Generating HMAC Challenge...' : '⚡ Get Challenge Phrase (90s TTL)'}
            </button>
          ) : (
            <div>
              <div className="challenge-box">
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--primary)', fontWeight: 700, marginBottom: '6px' }}>
                  CHALLENGE PHRASE TO SPEAK:
                </div>
                <div className="challenge-text">"{challenge.phrase}"</div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', marginTop: '10px' }}>
                  <span>Token: <code style={{ color: 'var(--primary)' }}>{challenge.token.substring(0, 18)}...</code></span>
                  <span style={{ color: timeLeft < 20 ? 'var(--danger)' : 'var(--warning)', fontWeight: 700 }}>
                    ⏱️ Expiration: {timeLeft}s remaining
                  </span>
                </div>

                <div className="countdown-bar-container">
                  <div
                    className="countdown-bar"
                    style={{
                      width: `${(timeLeft / 90) * 100}%`,
                      background: timeLeft < 20 ? 'var(--danger)' : 'var(--primary-gradient)'
                    }}
                  ></div>
                </div>
              </div>

              {isRecording && (
                <div className="visualizer-box">
                  <div className="audio-waves">
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                    <div className="wave-bar"></div>
                  </div>
                </div>
              )}

              <button
                className={`btn-record ${isRecording ? 'recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={verifying}
              >
                {isRecording
                  ? '🔴 Stop Recording & Submit Response'
                  : verifying
                  ? 'Verifying L2 → L1 → L3 Pipeline...'
                  : '🎙️ Speak Phrase & Verify'}
              </button>
            </div>
          )}

          {statusMsg && (
            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: statusMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
                border: `1px solid ${statusMsg.type === 'success' ? 'var(--success-border)' : 'var(--danger-border)'}`,
                color: statusMsg.type === 'success' ? 'var(--success)' : 'var(--danger)',
                fontSize: '0.9rem',
                fontWeight: 600
              }}
            >
              {statusMsg.text}
            </div>
          )}

          {verifyResult && (
            <div className={`result-card ${verifyResult.result}`}>
              <div className="result-header">
                <div>
                  <span className={`badge-result ${verifyResult.result}`}>
                    {verifyResult.result}
                  </span>
                  <span style={{ marginLeft: '12px', fontSize: '0.95rem', fontWeight: 600 }}>
                    {verifyResult.reason}
                  </span>
                </div>
                {verifyResult.layer_blocked && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--danger)', fontWeight: 700 }}>
                    🛑 Blocked at Layer {verifyResult.layer_blocked}
                  </div>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem', marginBottom: '1rem' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>L2 Deepfake Label</div>
                  <div style={{ fontWeight: 700, color: verifyResult.l2_label === 'spoof' ? 'var(--danger)' : 'var(--success)' }}>
                    {verifyResult.l2_label?.toUpperCase() || 'BONAFIDE'}
                  </div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>L2 Spoof Confidence</div>
                  <div style={{ fontWeight: 700 }}>{(verifyResult.l2_confidence * 100).toFixed(1)}%</div>
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>L1 Speaker Similarity</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{(verifyResult.l1_score * 100).toFixed(1)}%</div>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                FULL API RESPONSE JSON (POST /auth/verify)
              </div>
              <pre className="json-viewer">{JSON.stringify(verifyResult, null, 2)}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
