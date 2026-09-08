import React from 'react';

export function Navbar({ activeTab, setActiveTab, activeUser, isServerLive }) {
  const tabs = [
    { id: 'register', label: '1. Register' },
    { id: 'enroll', label: '2. Enroll Voice' },
    { id: 'login', label: '3. Switch User' },
    { id: 'verify', label: '4. Verify Auth' },
    { id: 'dashboard', label: '5. Dashboard' },
  ];

  return (
    <header className="navbar-header">
      <div className="navbar">
        <div className="nav-brand">
          <div className="brand-logo">AAA</div>
          <div>
            <span className="brand-title">AAA Engine</span>
            <span className="brand-tag" style={{ marginLeft: '8px' }}>L3 Adaptive</span>
          </div>
        </div>

        <div className="nav-right">
          <div className="server-badge">
            <span className={`dot-indicator ${isServerLive ? 'live' : 'mock'}`}></span>
            {isServerLive ? 'FastAPI Live' : 'Demo Mock Active'}
          </div>

          {activeUser && (
            <div className="user-chip">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f2fe' }}></span>
              <strong>{activeUser.name}</strong>
            </div>
          )}
        </div>
      </div>

      <nav className="tabs-container">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
