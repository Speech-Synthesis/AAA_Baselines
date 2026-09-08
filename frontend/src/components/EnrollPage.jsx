import React, { useState, useRef } from 'react';
import { enrollVoice } from '../api';

export function EnrollPage({ activeUser, onComplete }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [sampleCount, setSampleCount] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    if (!activeUser) {
      setStatusMsg({ type: 'error', text: 'Please register or select an active user first!' });
      return;
    }

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
        await handleAudioUpload(audioBlob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
      setStatusMsg(null);
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Microphone permission denied or unavailable' });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAudioUpload = async (audioBlob) => {
    setLoading(true);
    try {
      const res = await enrollVoice(activeUser.id, audioBlob);
      const newCount = res.sample_count || sampleCount + 1;
      setSampleCount(newCount);

      if (currentStep < 3) {
        setCurrentStep((prev) => prev + 1);
        setStatusMsg({
          type: 'success',
          text: `Sample ${currentStep} enrolled successfully! Total samples: ${newCount}. Speak next sample.`
        });
      } else {
        setStatusMsg({
          type: 'success',
          text: `🎉 All 3 voice samples enrolled! Voiceprint generated with sample count: ${newCount}.`
        });
        if (onComplete) setTimeout(() => onComplete(), 2000);
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Enrollment upload failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card">
      <div className="card-title">🎙️ Voiceprint Enrollment</div>
      <div className="card-subtitle">
        Record 3 spoken samples to build and adapt the user's ECAPA-TDNN speaker embedding (POST /auth/enroll)
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--warning)', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-md)' }}>
          ⚠️ No active user selected. Please go to the <strong>Register</strong> tab first.
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div>
              Active Enrollee: <strong>{activeUser.name}</strong>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Total Samples in DB: <strong>{sampleCount}</strong>
            </div>
          </div>

          <div className="progress-steps">
            {[1, 2, 3].map((step) => (
              <div
                key={step}
                className={`step-pill ${
                  step < currentStep ? 'completed' : step === currentStep ? 'active' : ''
                }`}
              >
                {step < currentStep ? `✓ Sample ${step}` : `Sample ${step}`}
              </div>
            ))}
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

          <div style={{ marginTop: '1.5rem' }}>
            <button
              className={`btn-record ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
            >
              {isRecording
                ? '🔴 Stop Recording (Release to Upload)'
                : loading
                ? 'Processing Embedding...'
                : `🎙️ Record Sample ${currentStep} of 3 (Min 3 Seconds)`}
            </button>
          </div>

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
        </>
      )}
    </div>
  );
}
