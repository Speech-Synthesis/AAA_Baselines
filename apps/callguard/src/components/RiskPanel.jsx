import React from 'react';

/**
 * RiskPanel Component
 * 
 * Displays AAA-VR vishing risk metrics for the active call.
 * 
 * Day 1 Scope:
 * - Component structure & clear placeholder/mock status
 * - Displays risk level (LOW/MEDIUM/HIGH), public reasons, recommended actions
 * - Safe outcome display (does NOT expose raw model scores)
 */
export default function RiskPanel({ riskData, onReevaluate, isAnalyzing }) {
  if (!riskData) {
    return (
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-title">
          <span>AAA-VR Vishing Risk Analysis</span>
          <span className="badge badge-blue">Day 1 Mock Mode</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No transcript segments submitted yet. Initiating baseline risk scan...
        </p>
      </div>
    );
  }

  const { risk_level, reason_public, recommended_action, detected_triggers, timestamp, _mock } = riskData;

  const getRiskBadge = (level) => {
    switch (level?.toUpperCase()) {
      case 'HIGH':
        return <span className="badge badge-high">HIGH RISK</span>;
      case 'MEDIUM':
        return <span className="badge badge-medium">MEDIUM RISK</span>;
      case 'LOW':
      default:
        return <span className="badge badge-low">LOW RISK</span>;
    }
  };

  return (
    <div className="card" style={{ marginBottom: '16px' }}>
      <div className="card-title">
        <span>AAA-VR Vishing Risk Panel</span>
        {getRiskBadge(risk_level)}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Public Reason Category
          </div>
          <div style={{ fontWeight: '600', fontSize: '0.9rem', color: 'var(--text-main)', marginTop: '2px' }}>
            {reason_public || 'ROUTINE_INQUIRY'}
          </div>
        </div>

        <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Recommended Protocol
          </div>
          <div style={{ fontWeight: '600', fontSize: '0.9rem', color: risk_level === 'HIGH' ? 'var(--risk-high)' : 'var(--risk-low)', marginTop: '2px' }}>
            {recommended_action || 'NONE'}
          </div>
        </div>

        {detected_triggers && detected_triggers.length > 0 && (
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>
              Detected Behavioral Triggers
            </div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {detected_triggers.map((trig, idx) => (
                <span key={idx} className="badge badge-medium" style={{ fontSize: '0.68rem' }}>
                  {trig}
                </span>
              ))}
            </div>
          </div>
        )}

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Updated: {timestamp ? new Date(timestamp).toLocaleTimeString() : 'Just now'}
            {_mock && ' • (Simulated Mock Adapter)'}
          </span>
          <button 
            className="btn btn-secondary btn-sm" 
            onClick={onReevaluate}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing...' : 'Rescan Transcript'}
          </button>
        </div>
      </div>
    </div>
  );
}
