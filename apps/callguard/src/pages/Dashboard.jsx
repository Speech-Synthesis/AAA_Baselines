import React from 'react';
import AuditHistory from '../components/AuditHistory';

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
                const isHighRisk = call.riskLevel === 'HIGH';
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
                      <span className={`badge ${isHighRisk ? 'badge-high' : 'badge-low'}`}>
                        {call.riskLevel} RISK
                      </span>
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
