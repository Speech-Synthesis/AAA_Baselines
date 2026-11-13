import React, { useState } from 'react';

/**
 * EscalationPanel Component
 * 
 * Allows call-centre agents to escalate suspicious interactions to Tier 2 Fraud Supervisors.
 * 
 * Day 1 Scope:
 * - Structural component with synthetic escalation state
 * - Strict non-sensitive note capture (no PII)
 */
export default function EscalationPanel({ callId, customerRef, onEscalate, initialStatus = "NORMAL" }) {
  const [escalationStatus, setEscalationStatus] = useState(initialStatus);
  const [note, setNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleEscalate = (e) => {
    e.preventDefault();
    if (!note.trim()) return;

    setIsSubmitting(true);
    setTimeout(() => {
      setEscalationStatus("ESCALATED_PENDING_SUPERVISOR");
      setIsSubmitting(false);
      if (onEscalate) {
        onEscalate({
          callId,
          customerRef,
          note,
          status: "ESCALATED_PENDING_SUPERVISOR",
          timestamp: new Date().toISOString()
        });
      }
    }, 400);
  };

  return (
    <div className="card" style={{ marginBottom: '16px' }}>
      <div className="card-title">
        <span>Human Review & Escalation</span>
        <span className={`badge ${escalationStatus === 'ESCALATED_PENDING_SUPERVISOR' ? 'badge-high' : 'badge-low'}`}>
          {escalationStatus === 'ESCALATED_PENDING_SUPERVISOR' ? 'ESCALATED' : 'STANDARD TIER 1'}
        </span>
      </div>

      {escalationStatus === 'ESCALATED_PENDING_SUPERVISOR' ? (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--risk-high)', padding: '14px', borderRadius: '6px' }}>
          <div style={{ fontWeight: '600', color: 'var(--risk-high)', fontSize: '0.88rem' }}>
            Escalated to Fraud Supervisor Tier 2
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Supervisor dispatched to monitor call session. Transaction hold applied.
          </p>
          <div style={{ marginTop: '8px', fontSize: '0.78rem', background: 'var(--bg-dark)', padding: '8px', borderRadius: '4px' }}>
            <strong>Agent Note:</strong> {note}
          </div>
        </div>
      ) : (
        <form onSubmit={handleEscalate}>
          <div className="form-group" style={{ marginBottom: '10px' }}>
            <label style={{ fontSize: '0.75rem' }}>Escalation Reason (Non-sensitive note only):</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. Caller pressured bypass of standard voice challenge"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              style={{ fontSize: '0.82rem' }}
              required
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-danger btn-sm" 
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={isSubmitting || !note.trim()}
          >
            {isSubmitting ? 'Escalating...' : 'Escalate for Human Review'}
          </button>
        </form>
      )}
    </div>
  );
}
