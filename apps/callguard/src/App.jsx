import React, { useState } from 'react';
import AgentLogin from './pages/AgentLogin';
import Dashboard from './pages/Dashboard';
import ActiveCall from './pages/ActiveCall';
import { demoAgents, demoCalls, demoAuditLogs } from './data/mockData';

export default function App() {
  const [currentAgent, setCurrentAgent] = useState(demoAgents[0]); // Default signed in for convenience
  const [activeCall, setActiveCall] = useState(null);
  const [calls, setCalls] = useState(demoCalls);
  const [auditLogs, setAuditLogs] = useState(demoAuditLogs);

  const handleLogin = (agent) => {
    setCurrentAgent(agent);
  };

  const handleLogout = () => {
    setCurrentAgent(null);
    setActiveCall(null);
  };

  const handleOpenCall = (call) => {
    setActiveCall(call);
  };

  const handleBackToDashboard = () => {
    setActiveCall(null);
  };

  const handleAddAuditLog = (newLog) => {
    setAuditLogs(prev => [newLog, ...prev]);
  };

  return (
    <div>
      {/* Strict Compliance Banner */}
      <div className="simulated-banner">
        <span>⚠️ SIMULATED CALL — DEMO DATA ONLY</span>
        <span className="banner-pill">SYNTHETIC BIOMETRICS & PROMPTS</span>
        <span className="banner-pill">TENANT: callcentre_demo</span>
      </div>

      {/* Main Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">CG</div>
          <div className="brand-text">
            <h1>CallGuard Console</h1>
            <p>Adaptive Voice Security & Vishing Mitigation</p>
          </div>
        </div>

        {currentAgent ? (
          <div className="header-user">
            <div className="user-badge">
              <div className="avatar">{currentAgent.avatar}</div>
              <div className="user-info">
                <div className="user-name">{currentAgent.name}</div>
                <div className="user-role">{currentAgent.role}</div>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
              Sign Out
            </button>
          </div>
        ) : (
          <span className="badge badge-medium">Not Signed In</span>
        )}
      </header>

      {/* Main Content Router */}
      <main>
        {!currentAgent ? (
          <AgentLogin onLogin={handleLogin} />
        ) : activeCall ? (
          <ActiveCall
            call={activeCall}
            onBackToDashboard={handleBackToDashboard}
            onAddAuditLog={handleAddAuditLog}
            allAuditLogs={auditLogs}
          />
        ) : (
          <Dashboard
            agent={currentAgent}
            calls={calls}
            onOpenCall={handleOpenCall}
            auditLogs={auditLogs}
          />
        )}
      </main>
    </div>
  );
}
