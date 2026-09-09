import React, { useState } from 'react';

export function LoginPage({ activeUser, setActiveUser, registeredUsers, onSelectUser }) {
  const [lookupEmail, setLookupEmail] = useState('');
  const [statusMsg, setStatusMsg] = useState(null);

  const handleLookup = (e) => {
    e.preventDefault();
    if (!lookupEmail.trim()) return;

    const found = registeredUsers.find(
      (u) => u.email.toLowerCase() === lookupEmail.trim().toLowerCase() || u.id === lookupEmail.trim()
    );

    if (found) {
      setActiveUser(found);
      setStatusMsg({ type: 'success', text: `Switched active session to ${found.name}` });
      if (onSelectUser) onSelectUser(found);
    } else {
      setStatusMsg({ type: 'error', text: 'Registered identity not found. Please register first.' });
    }
  };

  return (
    <div className="saas-card">
      <div className="card-title-lg">Identity Session Selector</div>
      <div className="card-subtitle-text">
        Select or lookup an enrolled identity to test voice authentication pipeline
      </div>

      <form onSubmit={handleLookup}>
        <div className="saas-input-group">
          <label className="saas-label">Email or User UUID</label>
          <input
            type="text"
            className="saas-input"
            placeholder="Enter registered email address or user UUID..."
            value={lookupEmail}
            onChange={(e) => setLookupEmail(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-saas-primary">
          Lookup Identity & Activate Session
        </button>
      </form>

      {statusMsg && (
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-lg)',
            background: statusMsg.type === 'success' ? 'var(--success-light)' : 'var(--danger-light)',
            border: `1px solid ${statusMsg.type === 'success' ? 'var(--success-green)' : 'var(--danger-red)'}`,
            color: statusMsg.type === 'success' ? 'var(--success-green)' : 'var(--danger-red)',
            fontSize: '0.92rem',
            fontWeight: 700
          }}
        >
          {statusMsg.text}
        </div>
      )}

      <div style={{ marginTop: '2.5rem' }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '1rem' }}>
          Enrolled Identities Directory ({registeredUsers.length})
        </div>

        {registeredUsers.length === 0 ? (
          <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            No registered users found. Go to Register tab to create one!
          </div>
        ) : (
          <div className="light-user-grid">
            {registeredUsers.map((u) => (
              <div
                key={u.id}
                className={`light-user-card ${activeUser?.id === u.id ? 'selected' : ''}`}
                onClick={() => {
                  setActiveUser(u);
                  setStatusMsg({ type: 'success', text: `Switched active user to ${u.name}` });
                  if (onSelectUser) onSelectUser(u);
                }}
              >
                <div className="user-avatar-initials">
                  {u.name.charAt(0).toUpperCase()}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{u.name}</span>
                    {activeUser?.id === u.id && (
                      <span style={{ fontSize: '0.72rem', background: 'var(--primary-blue)', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontWeight: 800 }}>ACTIVE</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{u.email}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
