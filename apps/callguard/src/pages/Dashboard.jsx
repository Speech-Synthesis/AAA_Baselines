import React from 'react';
import AuditHistory from '../components/AuditHistory';

/**
 * Helper to render consistently styled risk badges in the queue table.
 * Supports LOW, MEDIUM, HIGH, and CRITICAL risk levels.
 */
function getQueueRiskBadge(level) {
  const normLevel = typeof level === 'string' ? level.toUpperCase() : 'UNKNOWN';
  switch (normLevel) {
    case 'CRITICAL':
      return (
        <span
          className="badge"
          style={{
            background: 'rgba(239, 68, 68, 0.35)',
            color: '#ff4d4f',
            border: '2px solid #ef4444',
            boxShadow: '0 0 8px rgba(239, 68, 68, 0.5)',
            fontWeight: '700'
          }}
        >
          CRITICAL RISK
        </span>
      );
    case 'HIGH':
      return <span className="badge badge-high">HIGH RISK</span>;
    case 'MEDIUM':
      return <span className="badge badge-medium">MEDIUM RISK</span>;
    case 'LOW':
      return <span className="badge badge-low">LOW RISK</span>;
    default:
      return <span className="badge badge-low">{normLevel} RISK</span>;
  }
}

/**
 * Dashboard Page
 *
 * Simulated Agent Call Queue and Overview.
 */
export default function Dashboard({ agent, calls, onOpenCall, auditLogs }) {
  return (
    <div className="container">
      {/* Agent Overview Bar */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem' }}>Welcome, {agent.name}</h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Assigned Queue: <strong>{agent.queue}</strong> • Shift ID: <code>SHF-2026-N5</code>
            </p>
          </div>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Calls in Queue</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: 'var(--primary-light)' }}>{calls.length}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Tenant Binding</div>
              <span className="badge badge-blue">callcentre_demo</span>
            </div>
          </div>
        </div>
      </div>

      {/* Simulated Incoming Call Queue */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">
          <span>Simulated Priority Call Queue</span>
          <span className="badge badge-medium">SIMULATED QUEUE — DEMO ONLY</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Call ID</th>
                <th>Customer Ref</th>
                <th>Scenario / Purpose</th>
                <th>Channel</th>
                <th>Status</th>
                <th>Vishing Risk Preview</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((call) => {
                return (
                  <tr key={call.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: '600' }}>{call.id}</td>
                    <td>
                      <span style={{ fontWeight: '500' }}>{call.customerRef}</span>
                    </td>
                    <td>
                      <div style={{ fontWeight: '600', fontSize: '0.84rem' }}>{call.scenarioName}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{call.scenarioDescription}</div>
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{call.channel}</td>
                    <td>
                      <span className={`badge ${call.status === 'IN_PROGRESS' ? 'badge-blue' : 'badge-low'}`}>
                        {call.status}
                      </span>
                    </td>
                    <td>
                      {getQueueRiskBadge(call.riskLevel)}
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => onOpenCall(call)}
                      >
                        Open Call Console
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Global Audit History */}
      <AuditHistory logs={auditLogs} />
    </div>
  );
}
