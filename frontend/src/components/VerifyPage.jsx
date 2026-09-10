import React, { useState, useEffect, useRef } from 'react';
import { getChallenge, verifyVoice } from '../api';
import { convertBlobTo16kHzWav } from '../utils/audioEncoder';

export function VerifyPage({ activeUser, onComplete }) {
  const [challenge, setChallenge] = useState(null);
  const [loadingChallenge, setLoadingChallenge] = useState(false);
  const [timeLeft, setTimeLeft] = useState(90);
  const [isRecording, setIsRecording] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);
  const [statusMsg, setStatusMsg] = useState(null);

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
            setStatusMsg({ type: 'error', text: 'Challenge token expired (90s TTL limit reached). Please request a fresh challenge.' });
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
        const rawBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Convert to 16kHz Mono WAV Blob for 100% backend compatibility
        const wavBlob = await convertBlobTo16kHzWav(rawBlob);
        await handleVerifySubmit(wavBlob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setStatusMsg(null);
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Microphone access denied or unavailable' });
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
      const res = await verifyVoice(activeUser.id, challenge.token, audioBlob);
      setVerifyResult(res);
      setChallenge(null);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Verification pipeline failed' });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="saas-card">
      <div className="card-title-lg">Adaptive Authentication Protocol</div>
      <div className="card-subtitle-text">
        Deepfake Detection (L2) → Phrase Match (ASR) → Speaker Verification (L1) → Token (L3)
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.75rem', textAlign: 'center', color: 'var(--warning-amber)', background: '#fffbeb', borderRadius: 'var(--radius-lg)', border: '1px solid #fde68a', fontWeight: 600 }}>
          No active user selected. Please complete Register first.
        </div>
      ) : (
        <>
          <div style={{ marginBottom: '1.5rem' }}>
            <div>
              Target Identity: <strong style={{ color: 'var(--text-dark)' }}>{activeUser.name}</strong> ({activeUser.email})
            </div>
          </div>

          {!challenge ? (
            <button className="btn-saas-primary" onClick={fetchNewChallenge} disabled={loadingChallenge}>
              {loadingChallenge ? 'Signing HMAC-SHA256 Token...' : 'Request Challenge Phrase (90s TTL)'}
            </button>
          ) : (
            <div>
              <div className="light-challenge-hero">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--primary-blue)', fontWeight: 700 }}>
                  CHALLENGE PHRASE TO SPEAK
                </div>
                <div className="challenge-text-display">"{challenge.phrase}"</div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', marginTop: '0.75rem' }}>
                  <span>Token: <code>{challenge.token.substring(0, 22)}...</code></span>
                  <span style={{ color: timeLeft < 20 ? 'var(--danger-red)' : 'var(--warning-amber)', fontWeight: 700 }}>
                    Expiration: {timeLeft}s remaining
                  </span>
                </div>

                <div style={{ width: '100%', height: '6px', background: 'rgba(37, 99, 235, 0.15)', borderRadius: '3px', overflow: 'hidden', marginTop: '0.75rem' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${(timeLeft / 90) * 100}%`,
                      background: timeLeft < 20 ? 'var(--danger-red)' : 'var(--primary-blue)',
                      transition: 'width 1s linear'
                    }}
                  ></div>
                </div>
              </div>

              {isRecording && (
                <div className="light-spectrum-box">
                  <div className="light-bars-flex">
                    {Array.from({ length: 16 }).map((_, i) => (
                      <div key={i} className="light-bar"></div>
                    ))}
                  </div>
                </div>
              )}

              <button
                className={`btn-saas-record ${isRecording ? 'active-recording' : ''}`}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={verifying}
              >
                {isRecording
                  ? 'Stop Recording & Submit Response'
                  : verifying
                  ? 'Processing L2 → ASR → L1 → L3 Pipeline...'
                  : 'Speak Challenge Phrase & Authenticate'}
              </button>
            </div>
          )}

          {statusMsg && (
            <div
              style={{
                marginTop: '1.5rem',
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-lg)',
                background: statusMsg.type === 'success' ? 'var(--success-light)' : 'var(--danger-light)',
                border: `1px solid ${statusMsg.type === 'success' ? 'var(--success-green)' : 'var(--danger-red)'}`,
                color: statusMsg.type === 'success' ? 'var(--success-green)' : 'var(--danger-red)',
                fontSize: '0.92rem',
                fontWeight: 700
              }}
            >
              {statusMsg.text}
            </div>
          )}

          {verifyResult && (
            <div className={`light-decision-card ${verifyResult.result}`}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className={`badge-decision-light ${verifyResult.result}`}>
                    {verifyResult.result}
                  </span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                    {verifyResult.reason}
                  </span>
                </div>

                {verifyResult.layer_blocked && (
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--danger-red)', fontWeight: 700 }}>
                    Blocked at Layer {verifyResult.layer_blocked}
                  </div>
                )}
              </div>

              <div className="saas-metrics-grid">
                <div className="saas-stat-card">
                  <div className="saas-stat-label">L2 Deepfake Label</div>
                  <div className="saas-stat-val" style={{ color: verifyResult.l2_label === 'spoof' ? 'var(--danger-red)' : 'var(--success-green)' }}>
                    {verifyResult.l2_label?.toUpperCase() || 'BONAFIDE'}
                  </div>
                </div>

                <div className="saas-stat-card">
                  <div className="saas-stat-label">L2 Spoof Confidence</div>
                  <div className="saas-stat-val">
                    {(verifyResult.l2_confidence * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="saas-stat-card">
                  <div className="saas-stat-label">L1 Speaker Similarity</div>
                  <div className="saas-stat-val" style={{ color: 'var(--primary-blue)' }}>
                    {(verifyResult.l1_score * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="saas-stat-card">
                  <div className="saas-stat-label">L3 ASR Phrase Match</div>
                  <div className="saas-stat-val" style={{ color: verifyResult.asr_similarity >= 0.6 ? 'var(--success-green)' : 'var(--danger-red)' }}>
                    {verifyResult.asr_similarity != null ? `${(verifyResult.asr_similarity * 100).toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
              </div>

              {verifyResult.asr_transcript && (
                <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'var(--bg-light)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.35rem' }}>
                    ASR Transcription (Whisper)
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-dark)' }}>
                    "{verifyResult.asr_transcript}"
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1.5rem', marginBottom: '0.5rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  POST /auth/verify Full REST Response JSON
                </div>
                {onComplete && (
                  <button className="btn-saas-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={onComplete}>
                    Proceed to Analytics →
                  </button>
                )}
              </div>

              <pre className="light-inspector-box">{JSON.stringify(verifyResult, null, 2)}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
