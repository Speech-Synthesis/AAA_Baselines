import React from 'react'

/**
 * Transaction List Component
 * Displays a list of transactions for an account.
 */

function TransactionList({ transactions }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="no-transactions">
        <p>No transactions to display.</p>
      </div>
    )
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'credit': return '&#x2B06;'
      case 'debit': return '&#x2B07;'
      case 'transfer': return '&#x21C4;'
      default: return '&#x2022;'
    }
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="transaction-list">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Type</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(tx => (
            <tr key={tx.id} className={tx.type}>
              <td>{formatDate(tx.date)}</td>
              <td>
                <span dangerouslySetInnerHTML={{ __html: getTypeIcon(tx.type) }} />
                {' '}{tx.description}
              </td>
              <td className="tx-type">{tx.type}</td>
              <td className={`tx-amount ${tx.type}`}>
                {tx.type === 'debit' ? '-' : '+'}${Math.abs(tx.amount).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TransactionList
