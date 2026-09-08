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
      setStatusMsg({ type: 'success', text: `Logged in as ${found.name}` });
      if (onSelectUser) onSelectUser(found);
    } else {
      setStatusMsg({ type: 'error', text: 'User email/ID not found. Please register first.' });
    }
  };

  return (
    <div className="glass-card">
      <div className="card-title">🔑 Switch / Lookup Enrolled User</div>
      <div className="card-subtitle">
        Select or lookup an enrolled identity to test voice challenge authentication (Demo mode)
      </div>

      <form onSubmit={handleLookup}>
        <div className="form-group">
          <label>Email or User UUID Lookup</label>
          <input
            type="text"
            className="form-input"
            placeholder="Enter registered email address..."
            value={lookupEmail}
            onChange={(e) => setLookupEmail(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-primary">
          Lookup & Set Active Session
        </button>
      </form>

      {statusMsg && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: statusMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
            border: `1px solid ${statusMsg.type === 'success' ? 'var(--success-border)' : 'var(--danger-border)'}`,
            color: statusMsg.type === 'success' ? 'var(--success)' : 'var(--danger)',
            fontSize: '0.9rem',
            fontWeight: 600
          }}
        >
          {statusMsg.text}
        </div>
      )}

      <div style={{ marginTop: '2rem' }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-muted)' }}>
          AVAILABLE ENROLLED USERS
        </div>

        {registeredUsers.length === 0 ? (
          <div style={{ fontSize: '0.88rem', color: 'var(--text-dim)' }}>
            No registered users in current session. Go to Register tab to create one!
          </div>
        ) : (
          <div className="user-grid">
            {registeredUsers.map((u) => (
              <div
                key={u.id}
                className={`user-card ${activeUser?.id === u.id ? 'selected' : ''}`}
                onClick={() => {
                  setActiveUser(u);
                  setStatusMsg({ type: 'success', text: `Switched active user to ${u.name}` });
                  if (onSelectUser) onSelectUser(u);
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 700 }}>{u.name}</span>
                  {activeUser?.id === u.id && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 700 }}>ACTIVE</span>
                  )}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>{u.email}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
