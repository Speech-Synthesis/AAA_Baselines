import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import TransactionList from '../components/TransactionList.jsx'
import RiskPanel from '../components/RiskPanel.jsx'
import { DEMO_TRANSACTIONS, DEMO_BENEFICIARIES } from '../data/mockData.js'

/**
 * Banking Shield Transactions Page
 *
 * Transaction simulation per HOST_APPS.md:
 * - View balance
 * - Initiate mock transfer
 * - Add beneficiary
 * - Risk-based step-up for high-risk actions
 */

function Transactions({ user, onLogout }) {
  const navigate = useNavigate()
  const [selectedAccount, setSelectedAccount] = useState(user.accounts[0])
  const [showTransferModal, setShowTransferModal] = useState(false)
  const [transferData, setTransferData] = useState({
    beneficiary: '',
    amount: '',
    description: ''
  })
  const [riskAssessment, setRiskAssessment] = useState(null)
  const [verificationRequired, setVerificationRequired] = useState(false)

  const handleTransferSubmit = async (e) => {
    e.preventDefault()

    const amount = parseFloat(transferData.amount)

    // Risk assessment based on amount
    let riskLevel = 'LOW'
    let requiresVoice = false

    if (amount > 10000) {
      riskLevel = 'HIGH'
      requiresVoice = true
    } else if (amount > 5000) {
      riskLevel = 'MEDIUM'
      requiresVoice = user.hasVoiceprint // Only if enrolled
    }

    setRiskAssessment({
      risk_level: riskLevel,
      amount: amount,
      beneficiary: transferData.beneficiary,
      recommended_action: requiresVoice ? 'STEP_UP' : 'APPROVE',
      reason: requiresVoice ?
        'High-value transfer requires voice authentication' :
        'Transaction within normal limits'
    })

    if (requiresVoice && user.hasVoiceprint) {
      setVerificationRequired(true)
    } else if (requiresVoice && !user.hasVoiceprint) {
      alert('Voice enrollment required for high-value transfers. Please enroll first.')
      navigate('/enrollment')
    } else {
      // Low risk - approve directly
      alert(`Transfer of $${amount.toLocaleString()} approved!`)
      setShowTransferModal(false)
      setTransferData({ beneficiary: '', amount: '', description: '' })
      setRiskAssessment(null)
    }
  }

  const handleVoiceVerifyClick = () => {
    // Store transfer context in session for verification page
    sessionStorage.setItem('pendingTransfer', JSON.stringify({
      ...transferData,
      amount: parseFloat(transferData.amount)
    }))
    navigate('/verify')
  }

  return (
    <div className="transactions-page">
      <header className="page-header">
        <div className="header-left">
          <Link to="/dashboard" className="back-link">&larr; Dashboard</Link>
          <h1>Transactions</h1>
        </div>
        <div className="header-right">
          <span className="user-name">{user.name}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="transactions-content">
        <div className="transactions-grid">
          {/* Account Selector */}
          <section className="card account-selector">
            <h2>Select Account</h2>
            <div className="account-tabs">
              {user.accounts.map(acc => (
                <button
                  key={acc.id}
                  className={`account-tab ${selectedAccount.id === acc.id ? 'active' : ''}`}
                  onClick={() => setSelectedAccount(acc)}
                >
                  <span className="acc-name">{acc.name}</span>
                  <span className="acc-balance">${acc.balance.toLocaleString()}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Transaction Actions */}
          <section className="card actions-panel">
            <h2>Actions</h2>
            <div className="action-buttons">
              <button
                className="action-btn primary"
                onClick={() => setShowTransferModal(true)}
              >
                &#x1F4B8; New Transfer
              </button>
              <button className="action-btn" onClick={() => alert('Feature coming soon')}>
                &#x1F4DD; Download Statement
              </button>
            </div>
          </section>

          {/* Transaction History */}
          <section className="card transactions-list">
            <h2>Recent Transactions</h2>
            <TransactionList
              transactions={DEMO_TRANSACTIONS.filter(
                t => t.accountId === selectedAccount.id
              )}
            />
          </section>

          {/* Risk Assessment Panel */}
          {riskAssessment && (
            <section className="card risk-panel-container">
              <RiskPanel
                assessment={riskAssessment}
                onClose={() => setRiskAssessment(null)}
              />
              {verificationRequired && (
                <div className="verification-prompt">
                  <p>Voice verification required for this transaction.</p>
                  <button
                    className="verify-btn"
                    onClick={handleVoiceVerifyClick}
                  >
                    &#x1F3A4; Verify with Voice
                  </button>
                </div>
              )}
            </section>
          )}
        </div>
      </main>

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="modal-overlay">
          <div className="modal transfer-modal">
            <h2>New Transfer</h2>
            <form onSubmit={handleTransferSubmit}>
              <div className="form-group">
                <label>From Account</label>
                <select disabled>
                  <option>{selectedAccount.name} - ${selectedAccount.balance.toLocaleString()}</option>
                </select>
              </div>

              <div className="form-group">
                <label>Beneficiary</label>
                <select
                  value={transferData.beneficiary}
                  onChange={(e) => setTransferData({...transferData, beneficiary: e.target.value})}
                  required
                >
                  <option value="">Select beneficiary...</option>
                  {DEMO_BENEFICIARIES.map(b => (
                    <option key={b.id} value={b.name}>{b.name} - {b.bank}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Amount ($)</label>
                <input
                  type="number"
                  min="1"
                  max={selectedAccount.balance}
                  value={transferData.amount}
                  onChange={(e) => setTransferData({...transferData, amount: e.target.value})}
                  placeholder="Enter amount"
                  required
                />
                <small className="hint">
                  Transfers over $10,000 require voice verification
                </small>
              </div>

              <div className="form-group">
                <label>Description</label>
                <input
                  type="text"
                  value={transferData.description}
                  onChange={(e) => setTransferData({...transferData, description: e.target.value})}
                  placeholder="Optional description"
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowTransferModal(false)
                    setRiskAssessment(null)
                    setVerificationRequired(false)
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Continue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Transactions
