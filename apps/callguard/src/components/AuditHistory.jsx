import React from 'react';

/**
 * AuditHistory Component
 * 
 * Displays historical verification and security events for compliance.
 * 
 * Strict Security Boundary:
 * - Displays request ID, public outcome, risk level, timestamp, and safe action.
 * - NEVER displays raw speaker embeddings, cosine similarity, or Wav2Vec2 confidence floats.
 */
export default function AuditHistory({ logs = [] }) {
  return (
    <div className="card">
      <div className="card-title">
        <span>Security & Verification Audit Log</span>
        <span className="badge badge-blue">Protected Biometric Vault</span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Request ID</th>
              <th>Customer Ref</th>
              <th>Tenant</th>
              <th>Decision</th>
              <th>Risk Level</th>
              <th>Public Reason</th>
              <th>Timestamp</th>
              <th>Action Taken</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No audit events recorded for current session.
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const isApprove = log.decision === 'APPROVE';
                return (
                  <tr key={log.id || log.requestId}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>
                      {log.requestId || log.id}
                    </td>
                    <td>{log.customerRef}</td>
                    <td>
                      <span className="badge" style={{ background: '#334155' }}>
                        {log.tenantId || 'callcentre_demo'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${isApprove ? 'badge-low' : 'badge-high'}`}>
                        {log.decision}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${log.riskLevel === 'HIGH' ? 'badge-high' : 'badge-low'}`}>
                        {log.riskLevel}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {log.reasonPublic}
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td style={{ fontSize: '0.82rem' }}>
                      {log.actionTaken || 'Challenge session concluded'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
