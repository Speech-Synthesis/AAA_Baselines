import React, { useState } from 'react';
import { demoAgents } from '../data/mockData';

/**
 * AgentLogin Page
 * 
 * Simulated Agent Login for CallGuard console.
 * Strictly demo-only credential check.
 */
export default function AgentLogin({ onLogin }) {
  const [selectedAgentId, setSelectedAgentId] = useState(demoAgents[0].id);
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!password) {
      setError("Please enter demo password.");
      return;
    }
    const agent = demoAgents.find(a => a.id === selectedAgentId);
    if (agent) {
      onLogin(agent);
    } else {
      setError("Invalid agent profile selected.");
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-header">
          <div style={{ display: 'inline-flex', padding: '12px', background: 'var(--primary-dark)', borderRadius: '12px', marginBottom: '8px' }}>
            <span style={{ fontSize: '1.8rem' }}>🛡️</span>
          </div>
          <h2>CallGuard Agent Portal</h2>
          <p>Adaptive Voice Security & Vishing Defense</p>
        </div>

        <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid var(--primary-light)', padding: '10px 14px', borderRadius: '6px', marginBottom: '18px', fontSize: '0.78rem' }}>
          <strong>DEMO ENVIRONMENT:</strong> Pre-seeded operator accounts for Day 1 demonstration.
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--risk-high)', color: 'var(--risk-high)', padding: '10px', borderRadius: '6px', marginBottom: '14px', fontSize: '0.8rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Select Agent Identity:</label>
            <select
              className="form-control"
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
            >
              {demoAgents.map(agent => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} — {agent.role} ({agent.username})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Demo Password:</label>
            <input
              type="password"
              className="form-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter demo123"
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '10px' }}>
            Sign In to CallGuard Console
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Powered by AAA Engine • Tenant: <code>callcentre_demo</code>
        </div>
      </div>
    </div>
  );
}
