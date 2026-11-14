import React from 'react';

/**
 * RiskPanel Component
 * 
 * Displays AAA-VR vishing risk metrics for the active call.
 * 
 * Complies with frozen AAA-VR contract (CALLGUARD_RISK_INTEGRATION_REPORT.md):
 * - Displays risk level (LOW / MEDIUM / HIGH / CRITICAL) with visually distinct CRITICAL state
 * - Renders public reason codes (risk_indicators) using safe metadata
 * - Displays recommended protocol actions (APPROVE / REVIEW / STEP_UP / DENY)
 * - Safe presentation: zero numerical confidence scores exposed to operators
 * - Does NOT expose raw acoustic scores, embeddings, or voiceprints
 */

const INDICATOR_LABELS = {
  URGENT_TRANSFER_REQUEST: 'Urgent Wire Demand',
  PRESSURE_TACTICS_DETECTED: 'Coercion / Legal Threat',
  ACCOUNT_NUMBER_MENTIONED: 'Sensitive Account Disclosure',
  CREDENTIAL_HARVESTING_ATTEMPT: 'Credential Request',
  UNVERIFIED_BENEFICIARY: 'Unverified Beneficiary',
  IMPERSONATION_ATTEMPT: 'False Authority Claim',
  VOICE_STRESS_ANOMALY: 'Acoustic Cadence Anomaly'
};

export default function RiskPanel({ riskData, onReevaluate, isAnalyzing }) {
  if (!riskData) {
    return (
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-title">
          <span>AAA-VR Vishing Risk Analysis</span>
          <span className="badge badge-blue">Day 3 Mock Mode</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No transcript segments submitted yet. Initiating baseline risk scan...
        </p>
      </div>
    );
  }

  // Safe field extraction with defensive fallbacks
  const risk_level = typeof riskData.risk_level === 'string' 
    ? riskData.risk_level.toUpperCase() 
    : 'UNKNOWN';

  const rawIndicators = riskData.risk_indicators || riskData.detected_triggers || [];
  const risk_indicators = Array.isArray(rawIndicators)
    ? rawIndicators
    : (typeof rawIndicators === 'string' && rawIndicators ? [rawIndicators] : []);

  const recommended_action = typeof riskData.recommended_action === 'string'
    ? riskData.recommended_action.toUpperCase()
    : 'APPROVE';

  const model_version = riskData.model_version || 'aaa-vr-transcript-risk-v1';
  const analyzed_at = riskData.analyzed_at || riskData.timestamp;
  const _mock = Boolean(riskData._mock);
  const request_id = riskData.request_id;
  const isCritical = risk_level === 'CRITICAL';

  const getRiskBadge = (level) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span 
            className="badge" 
            style={{ 
              background: 'rgba(239, 68, 68, 0.35)', 
              color: '#ff4d4f', 
              border: '2px solid #ef4444',
              boxShadow: '0 0 10px rgba(239, 68, 68, 0.6)',
              fontWeight: '800',
              letterSpacing: '0.06em'
            }}
          >
            CRITICAL RISK (THREAT DETECTED)
          </span>
        );
      case 'HIGH':
        return <span className="badge badge-high">HIGH RISK</span>;
      case 'MEDIUM':
        return <span className="badge badge-medium">MEDIUM RISK</span>;
      case 'LOW':
        return <span className="badge badge-low">LOW RISK</span>;
      default:
        return (
          <span 
            className="badge" 
            style={{ 
              background: 'rgba(148, 163, 184, 0.2)', 
              color: 'var(--text-muted)', 
              border: '1px solid var(--border)' 
            }}
          >
            {level || 'UNKNOWN'}
          </span>
        );
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'DENY':
        return 'var(--risk-high)';
      case 'STEP_UP':
        return '#f97316';
      case 'REVIEW':
        return 'var(--risk-medium)';
      case 'APPROVE':
        return 'var(--risk-low)';
      default:
        return 'var(--text-main)';
    }
  };

  const getActionDescription = (action) => {
    switch (action) {
      case 'DENY':
        return 'Severe threat / credential harvesting detected. Escalate immediately to Fraud Operations desk.';
      case 'STEP_UP':
        return 'Multiple risk markers present. Trigger AAA voice biometric challenge.';
      case 'REVIEW':
        return 'Single risk marker present. Prompt agent to exercise standard verification caution.';
      case 'APPROVE':
        return 'Normal call flow. No abnormal vishing signals detected.';
      default:
        return 'Proceed with standard operational protocol.';
    }
  };

  const cardStyle = {
    marginBottom: '16px',
    ...(isCritical ? {
      border: '2px solid #ef4444',
      boxShadow: '0 0 16px rgba(239, 68, 68, 0.3)',
      background: 'linear-gradient(180deg, rgba(239, 68, 68, 0.08) 0%, var(--bg-card) 100%)'
    } : {})
  };

  return (
    <div className="card" style={cardStyle}>
      <div className="card-title">
        <span>AAA-VR Vishing Risk Panel</span>
        {getRiskBadge(risk_level)}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Recommended Action Protocol */}
        <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Recommended Protocol Action
            </span>
            <span style={{ fontSize: '0.82rem', fontWeight: '700', color: getActionColor(recommended_action) }}>
              {recommended_action}
            </span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-main)', marginTop: '4px' }}>
            {getActionDescription(recommended_action)}
          </div>
        </div>

        {/* Public Risk Indicators */}
        <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '6px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
            Public Risk Indicators ({risk_indicators.length})
          </div>
          {risk_indicators.length === 0 ? (
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              None detected (Clean conversational flow)
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {risk_indicators.map((ind, idx) => {
                const isSevere = ind === 'CREDENTIAL_HARVESTING_ATTEMPT' || 
                  ind === 'IMPERSONATION_ATTEMPT' || 
                  ind === 'PRESSURE_TACTICS_DETECTED';
                return (
                  <span 
                    key={idx} 
                    className="badge" 
                    style={{ 
                      fontSize: '0.72rem',
                      background: isSevere ? 'rgba(239, 68, 68, 0.25)' : 'rgba(245, 158, 11, 0.25)',
                      color: isSevere ? 'var(--risk-high)' : 'var(--risk-medium)',
                      border: `1px solid ${isSevere ? 'var(--risk-high)' : 'var(--risk-medium)'}`
                    }}
                    title={ind}
                  >
                    {INDICATOR_LABELS[ind] || ind}
                  </span>
                );
              })}
            </div>
          )}
        </div>

        {/* Traceability & Model Metadata (Zero Caller Identity Leakage) */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            <div>
              Engine: <code>{model_version}</code>
            </div>
            <div>
              Updated: {analyzed_at ? new Date(analyzed_at).toLocaleTimeString() : 'Just now'}
              {_mock && ' • (Simulated Mock Adapter)'}
              {request_id && ` • Req: ${request_id.substring(0, 16)}`}
            </div>
          </div>
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
