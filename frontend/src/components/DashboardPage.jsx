import React, { useState, useEffect } from 'react';
import { getVoiceprintHistory, getAuthLogs } from '../api';

export function DashboardPage({ activeUser }) {
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (activeUser) {
      getVoiceprintHistory(activeUser.id).then(setHistory);
      getAuthLogs(activeUser.id).then(setLogs);
    } else {
      setHistory([]);
      setLogs([]);
    }
  }, [activeUser]);

  return (
    <div className="saas-card">
      <div className="card-title-lg">Biometric Voiceprint Analytics & Audit Logs</div>
      <div className="card-subtitle-text">
        Real-time monitoring of EMA voiceprint shifts (New = 0.8 * Old + 0.2 * Current) and authentication audit logs
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.75rem', textAlign: 'center', color: 'var(--warning-amber)', background: '#fffbeb', borderRadius: 'var(--radius-lg)', border: '1px solid #fde68a', fontWeight: 600 }}>
          Please select or register an identity to view individual voiceprint metrics.
        </div>
      ) : (
        <>
          <div className="saas-metrics-grid">
            <div className="saas-stat-card">
              <div className="saas-stat-label">Active User Identity</div>
              <div className="saas-stat-val" style={{ fontSize: '1.25rem', marginTop: '2px' }}>{activeUser.name}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--primary-blue)', marginTop: '4px' }}>
                {activeUser.id}
              </div>
            </div>

            <div className="saas-stat-card">
              <div className="saas-stat-label">Voiceprint Sample Count</div>
              <div className="saas-stat-val" style={{ color: 'var(--success-green)', marginTop: '2px' }}>
                {history.length > 0 ? history[0].sample_count : 3} Samples
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Adapted via EMA (α = 0.2)
              </div>
            </div>

            <div className="saas-stat-card">
              <div className="saas-stat-label">Embedding Architecture</div>
              <div className="saas-stat-val" style={{ color: 'var(--primary-blue)', marginTop: '2px' }}>
                192-dim
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                SpeechBrain ECAPA-TDNN
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '2.5rem', marginTop: '1.5rem' }}>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              Voiceprint Adaptation History (GET /users/:id/voiceprint-history)
            </div>

            <div style={{ background: '#ffffff', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
              {history.map((h, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '0.75rem 0',
                    borderBottom: i < history.length - 1 ? '1px solid var(--border-light)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', background: 'var(--primary-light)', color: 'var(--primary-blue)', padding: '3px 10px', borderRadius: '12px', fontWeight: 700 }}>
                      Update #{history.length - i}
                    </span>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                      Enrolled Samples: <strong style={{ color: 'var(--text-dark)' }}>{h.sample_count}</strong>
                    </span>
                  </div>

                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--primary-blue)' }}>
                    {new Date(h.updated_at).toLocaleDateString('en-GB')} {new Date(h.updated_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              Authentication Audit Log Timeline (auth_logs)
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table className="light-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Result</th>
                    <th>Blocked Layer</th>
                    <th>L2 Spoof Conf</th>
                    <th>L1 Similarity</th>
                    <th>Audit Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td>
                        <span className={`badge-tag-light ${log.result}`}>{log.result}</span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                        {log.layer_blocked ? `Layer ${log.layer_blocked}` : '—'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem' }}>
                        {(log.l2_confidence * 100).toFixed(1)}%
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem', color: 'var(--primary-blue)' }}>
                        {(log.l1_score * 100).toFixed(1)}%
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                        {log.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
