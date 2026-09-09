import React, { useState } from 'react';
import { registerUser } from '../api';

export function RegisterPage({ activeUser, setActiveUser, registeredUsers, setRegisteredUsers, refreshUsers, onComplete }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setStatusMsg({ type: 'error', text: 'Please enter both full name and email address' });
      return;
    }

    setLoading(true);
    setStatusMsg(null);

    try {
      const res = await registerUser(name, email);
      setStatusMsg({ type: 'success', text: `Identity registered successfully! Assigned UUID: ${res.user_id}` });

      setName('');
      setEmail('');

      // Refresh users list from database
      if (refreshUsers) await refreshUsers();

      if (onComplete) setTimeout(() => onComplete(), 1200);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Registration request failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="saas-card">
      <div className="card-title-lg">User Identity Registration</div>
      <div className="card-subtitle-text">
        Register a new identity profile in the AAA Engine database (Endpoint: <code>POST /auth/register</code>)
      </div>

      <form onSubmit={handleRegister}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <div className="saas-input-group">
            <label className="saas-label">Full Name</label>
            <input
              type="text"
              className="saas-input"
              placeholder="e.g. Dr. Aditya Sharma"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="saas-input-group">
            <label className="saas-label">Email Address</label>
            <input
              type="email"
              className="saas-input"
              placeholder="e.g. aditya@aaaengine.io"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginTop: '0.75rem' }}>
          <button type="submit" className="btn-saas-primary" disabled={loading}>
            {loading ? 'Processing Registration...' : 'Register Identity Profile'}
          </button>
        </div>
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
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justify: 'space-between'
          }}
        >
          <span>{statusMsg.text}</span>
          {statusMsg.type === 'success' && onComplete && (
            <button className="btn-saas-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={onComplete}>
              Proceed to Enroll Voice
            </button>
          )}
        </div>
      )}

      {registeredUsers.length > 0 && (
        <div style={{ marginTop: '2.5rem' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '1rem' }}>
            Registered Users ({registeredUsers.length})
          </div>

          <div className="light-user-grid">
            {registeredUsers.map((u) => (
              <div
                key={u.id}
                className={`light-user-card ${activeUser?.id === u.id ? 'selected' : ''}`}
                onClick={() => setActiveUser(u)}
              >
                <div className="user-avatar-initials">
                  {u.name.charAt(0).toUpperCase()}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {u.name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {u.email}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
