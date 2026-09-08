import React, { useState } from 'react';
import { registerUser } from '../api';

export function RegisterPage({ activeUser, setActiveUser, registeredUsers, setRegisteredUsers, onComplete }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setStatusMsg({ type: 'error', text: 'Please enter both name and email' });
      return;
    }

    setLoading(true);
    setStatusMsg(null);

    try {
      const res = await registerUser(name, email);
      const newUser = { id: res.user_id, name, email };
      
      setActiveUser(newUser);
      setRegisteredUsers((prev) => [newUser, ...prev.filter(u => u.id !== newUser.id)]);
      setStatusMsg({ type: 'success', text: `Registered successfully! Assigned User ID: ${res.user_id}` });
      
      setName('');
      setEmail('');

      if (onComplete) setTimeout(() => onComplete(), 1500);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Registration failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card">
      <div className="card-title">👤 User Registration</div>
      <div className="card-subtitle">
        Register a new identity in the AAA Engine voice database (POST /auth/register)
      </div>

      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label>Full Name</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Aditya Sharma"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Email Address</label>
          <input
            type="email"
            className="form-input"
            placeholder="e.g. aditya@aaaengine.io"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Registering...' : 'Register User'}
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

      {registeredUsers.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-muted)' }}>
            RECENTLY REGISTERED USERS
          </div>
          <div className="user-grid">
            {registeredUsers.map((u) => (
              <div
                key={u.id}
                className={`user-card ${activeUser?.id === u.id ? 'selected' : ''}`}
                onClick={() => setActiveUser(u)}
              >
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{u.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{u.email}</div>
                <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--primary)', marginTop: '4px' }}>
                  {u.id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
