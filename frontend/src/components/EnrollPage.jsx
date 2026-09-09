import React, { useState, useRef } from 'react';
import { enrollVoice } from '../api';
import { convertBlobTo16kHzWav } from '../utils/audioEncoder';

export function EnrollPage({ activeUser, onComplete }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [sampleCount, setSampleCount] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const [enrollmentComplete, setEnrollmentComplete] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    if (!activeUser) {
      setStatusMsg({ type: 'error', text: 'Please register or select an active user first' });
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
        const rawBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Convert to 16kHz Mono WAV Blob for 100% backend compatibility
        const wavBlob = await convertBlobTo16kHzWav(rawBlob);
        await handleAudioUpload(wavBlob);
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
          text: `Voice Sample ${currentStep} enrolled. Total samples: ${newCount}. Record next sample.`
        });
      } else {
        // Sample 3 complete - enrollment done
        setEnrollmentComplete(true);
        setStatusMsg({
          type: 'success',
          text: `Voiceprint enrollment complete. Built 192-dim embedding with ${newCount} total samples.`
        });
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Enrollment audio upload failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="saas-card">
      <div className="card-title-lg">Speaker Voiceprint Enrollment</div>
      <div className="card-subtitle-text">
        Record 3 audio samples (min 5s) to extract ECAPA-TDNN 192-dim acoustic embeddings (Endpoint: <code>POST /auth/enroll</code>)
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.75rem', textAlign: 'center', color: 'var(--warning-amber)', background: '#fffbeb', borderRadius: 'var(--radius-lg)', border: '1px solid #fde68a', fontWeight: 600 }}>
          No active user selected. Please complete Register first.
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              Active Enrollee: <strong style={{ color: 'var(--text-dark)' }}>{activeUser.name}</strong>
            </div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Database Sample Count: <strong style={{ color: 'var(--primary-blue)' }}>{sampleCount}</strong>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
            {[1, 2, 3].map((step) => (
              <div
                key={step}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  textAlign: 'center',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-light)',
                  background: step < currentStep ? 'var(--success-light)' : step === currentStep ? 'var(--primary-light)' : '#fff',
                  borderColor: step < currentStep ? 'var(--success-green)' : step === currentStep ? 'var(--primary-blue)' : 'var(--border-light)',
                  color: step < currentStep ? 'var(--success-green)' : step === currentStep ? 'var(--primary-blue)' : 'var(--text-muted)',
                  fontWeight: 700,
                  fontSize: '0.9rem'
                }}
              >
                {step < currentStep ? `Sample ${step} Complete` : `Sample ${step}`}
              </div>
            ))}
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

          <div style={{ marginTop: '1.5rem' }}>
            <button
              className={`btn-saas-record ${isRecording ? 'active-recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
            >
              {isRecording
                ? 'Stop Recording & Upload Sample'
                : loading
                ? 'Extracting 192-dim Embedding...'
                : `Record Voice Sample ${currentStep} of 3 (Min 5 Seconds)`}
            </button>
          </div>

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
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justify: 'space-between'
              }}
            >
              <span>{statusMsg.text}</span>
              {enrollmentComplete && onComplete && (
                <button className="btn-saas-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={onComplete}>
                  Proceed to Authenticate
                </button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
