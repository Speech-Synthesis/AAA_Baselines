import React from 'react'

/**
 * Account Card Component
 * Displays a single bank account summary.
 */

function AccountCard({ account }) {
  const getAccountIcon = (type) => {
    switch (type) {
      case 'checking': return '&#x1F4B3;'
      case 'savings': return '&#x1F3E6;'
      case 'investment': return '&#x1F4C8;'
      default: return '&#x1F4B0;'
    }
  }

  return (
    <div className="account-card">
      <div className="account-icon" dangerouslySetInnerHTML={{ __html: getAccountIcon(account.type) }} />
      <div className="account-details">
        <span className="account-name">{account.name}</span>
        <span className="account-number">****{account.number.slice(-4)}</span>
      </div>
      <div className="account-balance">
        <span className="balance-label">Balance</span>
        <span className="balance-amount">${account.balance.toLocaleString()}</span>
      </div>
    </div>
  )
}

export default AccountCard
