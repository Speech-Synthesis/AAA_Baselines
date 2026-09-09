import React, { useState } from 'react';

export function Sidebar({ activeTab, setActiveTab, activeUser, isServerLive }) {
  const [showAdvancedNav, setShowAdvancedNav] = useState(false);

  const processSteps = [
    { id: 'register', label: 'Register Identity' },
    { id: 'enroll', label: 'Enroll Voice' },
    { id: 'verify', label: 'Authenticate' },
    { id: 'dashboard', label: 'Audit & Analytics' },
  ];

  return (
    <aside className="saas-sidebar">
      <div>
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">AAA</div>
          <div>
            <div className="sidebar-brand-text">AAA Engine</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Adaptive Biometrics</div>
          </div>
        </div>

        <div style={{ margin: '1rem 0' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '0.75rem' }}>
            PROCESS FLOW WIZARD
          </div>

          <div className="sidebar-menu-list">
            {processSteps.map((step) => (
              <button
                key={step.id}
                className={`sidebar-menu-item ${activeTab === step.id ? 'active' : ''}`}
                onClick={() => setActiveTab(step.id)}
              >
                <span>{step.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Collapsible Advanced Navigation */}
        <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-light)' }}>
          <button
            onClick={() => setShowAdvancedNav(!showAdvancedNav)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}
          >
            <span>ADVANCED OPTIONS</span>
            <span>{showAdvancedNav ? '▲' : '▼'}</span>
          </button>

          {showAdvancedNav && (
            <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <button
                className={`sidebar-menu-item ${activeTab === 'login' ? 'active' : ''}`}
                onClick={() => setActiveTab('login')}
              >
                <span>Switch Identity</span>
              </button>
            </div>
          )}
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: isServerLive ? 'var(--success-green)' : 'var(--warning-amber)' }}></span>
          <span>{isServerLive ? 'FastAPI Server Live' : 'Demo Mode Active'}</span>
        </div>

        {activeUser && (
          <div className="sidebar-user-card">
            <div className="user-avatar-initials">
              {activeUser.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {activeUser.name}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {activeUser.email}
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

export function HeaderStepper({ activeTab, setActiveTab }) {
  const steps = [
    { id: 'register', label: 'Register' },
    { id: 'enroll', label: 'Enroll Voice' },
    { id: 'verify', label: 'Authenticate' },
    { id: 'dashboard', label: 'Analytics' },
  ];

  return (
    <div className="process-stepper-bar">
      {steps.map((s, idx) => {
        const isCurrent = activeTab === s.id;
        return (
          <React.Fragment key={s.id}>
            <div
              className={`step-flow-item ${isCurrent ? 'active' : ''}`}
              style={{ cursor: 'pointer' }}
              onClick={() => setActiveTab(s.id)}
            >
              <div className="step-flow-dot"></div>
              <span>{s.label}</span>
            </div>
            {idx < steps.length - 1 && <span className="step-flow-arrow">›</span>}
          </React.Fragment>
        );
      })}
    </div>
  );
}
