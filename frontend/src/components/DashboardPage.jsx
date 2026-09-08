import React, { useState, useEffect } from 'react';
import { getVoiceprintHistory, getMockStore } from '../api';

export function DashboardPage({ activeUser }) {
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (activeUser) {
      getVoiceprintHistory(activeUser.id).then(setHistory);
    }
    setLogs(getMockStore().logs);
  }, [activeUser]);

  return (
    <div className="glass-card">
      <div className="card-title">📊 Adaptive Voiceprint & Auth Audit Dashboard</div>
      <div className="card-subtitle">
        Real-time monitoring of EMA voiceprint shifts and pipeline authentication logs
      </div>

      {!activeUser ? (
        <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--warning)', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-md)' }}>
          ⚠️ Please select or register a user to view individual voiceprint analytics.
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ACTIVE USER IDENTITY</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px' }}>{activeUser.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{activeUser.id}</div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>VOICEPRINT SAMPLE COUNT</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--success)', marginTop: '4px' }}>
                {history.length > 0 ? history[0].sample_count : 3} Samples
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Updated with EMA (α=0.2)</div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', padding: '1.25rem', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>EMBEDDING DIMENSION</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary)', marginTop: '4px' }}>192-dim</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ECAPA-TDNN Architecture</div>
            </div>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              📈 Voiceprint History & Adaptation Log (GET /users/:id/voiceprint-history)
            </div>
            <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
              {history.map((h, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: i < history.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                  <div>
                    <span style={{ fontWeight: 600 }}>Update #{history.length - i}</span>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginLeft: '12px' }}>
                      Sample Count: {h.sample_count}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}>
                    {new Date(h.updated_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              📜 Recent Pipeline Authentication Audit Logs (auth_logs)
            </div>
            <table className="logs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Result</th>
                  <th>Blocked Layer</th>
                  <th>L2 Spoof Conf</th>
                  <th>L1 Similarity</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                      {new Date(log.created_at).toLocaleTimeString()}
                    </td>
                    <td>
                      <span className={`status-badge-sm ${log.result}`}>{log.result}</span>
                    </td>
                    <td>{log.layer_blocked ? `Layer ${log.layer_blocked}` : '—'}</td>
                    <td>{(log.l2_confidence * 100).toFixed(1)}%</td>
                    <td>{(log.l1_score * 100).toFixed(1)}%</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>{log.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
