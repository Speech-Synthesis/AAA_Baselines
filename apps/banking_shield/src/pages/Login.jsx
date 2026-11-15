import React, { useState } from 'react'
import { DEMO_ACCOUNTS } from '../data/mockData.js'

/**
 * Banking Shield Login Page
 *
 * Mock login with seeded demo accounts.
 * No real identity provider required per HOST_APPS.md.
 */

function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Simulate authentication delay
    await new Promise(resolve => setTimeout(resolve, 500))

    // Check demo accounts
    const account = DEMO_ACCOUNTS.find(
      acc => acc.email === email && acc.password === password
    )

    if (account) {
      onLogin({
        id: account.id,
        name: account.name,
        email: account.email,
        accounts: account.accounts,
        hasVoiceprint: account.hasVoiceprint,
        userRef: account.userRef
      })
    } else {
      setError('Invalid email or password. Try: alice@bank.demo / demo123')
    }

    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <div className="shield-icon">&#x1F6E1;</div>
          <h1>Banking Shield</h1>
          <p className="subtitle">Secure Voice Authentication Demo</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alice@bank.demo"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="demo123"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="demo-accounts">
          <h3>Demo Accounts</h3>
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Password</th>
                <th>Voice Enrolled</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_ACCOUNTS.map(acc => (
                <tr key={acc.id}>
                  <td>{acc.email}</td>
                  <td>{acc.password}</td>
                  <td>{acc.hasVoiceprint ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="aaa-badge">
          <span>Powered by AAA Engine</span>
        </div>
      </div>
    </div>
  )
}

export default Login
