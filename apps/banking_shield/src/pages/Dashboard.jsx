import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AccountCard from '../components/AccountCard.jsx'
import AuditHistory from '../components/AuditHistory.jsx'
import { checkAAAHealth } from '../services/api.js'

/**
 * Banking Shield Dashboard
 *
 * Shows account overview, recent activity, and navigation.
 * Displays voice enrollment status and AAA health.
 */

function Dashboard({ user, onLogout }) {
  const navigate = useNavigate()
  const [aaaHealth, setAaaHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function checkHealth() {
      try {
        const health = await checkAAAHealth()
        setAaaHealth(health)
      } catch (err) {
        setAaaHealth({ status: 'UNHEALTHY', error: err.message })
      }
      setLoading(false)
    }
    checkHealth()
  }, [])

  const totalBalance = user.accounts.reduce((sum, acc) => sum + acc.balance, 0)

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-left">
          <span className="shield-icon">&#x1F6E1;</span>
          <h1>Banking Shield</h1>
        </div>
        <div className="header-right">
          <span className="user-name">Welcome, {user.name}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="dashboard-grid">
          {/* Account Overview */}
          <section className="card accounts-section">
            <h2>Your Accounts</h2>
            <div className="total-balance">
              <span className="label">Total Balance</span>
              <span className="amount">${totalBalance.toLocaleString()}</span>
            </div>
            <div className="accounts-list">
              {user.accounts.map(account => (
                <AccountCard key={account.id} account={account} />
              ))}
            </div>
          </section>

          {/* Quick Actions */}
          <section className="card actions-section">
            <h2>Quick Actions</h2>
            <div className="action-buttons">
              <Link to="/transactions" className="action-btn">
                <span className="icon">&#x1F4B8;</span>
                <span>Transfers</span>
              </Link>
              {user.hasVoiceprint ? (
                <Link to="/verify" className="action-btn">
                  <span className="icon">&#x1F3A4;</span>
                  <span>Voice Verify</span>
                </Link>
              ) : (
                <Link to="/enrollment" className="action-btn enroll">
                  <span className="icon">&#x1F3A4;</span>
                  <span>Enroll Voice</span>
                </Link>
              )}
              <button className="action-btn" onClick={() => alert('Feature coming soon')}>
                <span className="icon">&#x1F464;</span>
                <span>Beneficiaries</span>
              </button>
            </div>
          </section>

          {/* Voice Authentication Status */}
          <section className="card voice-status-section">
            <h2>Voice Authentication</h2>
            <div className="status-indicator">
              {user.hasVoiceprint ? (
                <div className="status enrolled">
                  <span className="status-icon">&#x2705;</span>
                  <div>
                    <strong>Voice Enrolled</strong>
                    <p>High-risk transactions will require voice verification</p>
                  </div>
                </div>
              ) : (
                <div className="status not-enrolled">
                  <span className="status-icon">&#x26A0;</span>
                  <div>
                    <strong>Voice Not Enrolled</strong>
                    <p>Enroll your voice for enhanced security</p>
                    <Link to="/enrollment" className="enroll-link">
                      Enroll Now
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* AAA Health Status */}
            <div className="aaa-health">
              <h3>AAA Engine Status</h3>
              {loading ? (
                <span className="loading">Checking...</span>
              ) : aaaHealth?.status === 'HEALTHY' ? (
                <span className="healthy">&#x2705; All systems operational</span>
              ) : (
                <span className="unhealthy">&#x26A0; Service degraded</span>
              )}
            </div>
          </section>

          {/* Recent Activity */}
          <section className="card activity-section">
            <h2>Security Activity</h2>
            <AuditHistory userRef={user.userRef} limit={5} />
          </section>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
