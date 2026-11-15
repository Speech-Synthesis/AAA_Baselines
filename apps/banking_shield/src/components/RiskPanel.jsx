import React from 'react'

/**
 * Risk Panel Component
 * Displays risk assessment for transactions and verifications.
 * Shows decision, public reason category, and recommended action.
 */

function RiskPanel({ assessment, onClose }) {
  const getRiskColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'LOW': return 'green'
      case 'MEDIUM': return 'orange'
      case 'HIGH': return 'red'
      case 'CRITICAL': return 'darkred'
      default: return 'gray'
    }
  }

  const getRiskIcon = (level) => {
    switch (level?.toUpperCase()) {
      case 'LOW': return '&#x2705;'
      case 'MEDIUM': return '&#x26A0;'
      case 'HIGH': return '&#x1F6A8;'
      case 'CRITICAL': return '&#x2620;'
      default: return '&#x2753;'
    }
  }

  const getActionBadge = (action) => {
    switch (action?.toUpperCase()) {
      case 'APPROVE': return { text: 'Approved', class: 'approve' }
      case 'DENY': return { text: 'Denied', class: 'deny' }
      case 'STEP_UP': return { text: 'Step-Up Required', class: 'step-up' }
      case 'REVIEW': return { text: 'Review Required', class: 'review' }
      default: return { text: action || 'Unknown', class: 'unknown' }
    }
  }

  const actionBadge = getActionBadge(assessment.recommended_action)

  return (
    <div className="risk-panel" style={{ borderLeftColor: getRiskColor(assessment.risk_level) }}>
      <div className="risk-header">
        <div className="risk-level">
          <span
            className="risk-icon"
            dangerouslySetInnerHTML={{ __html: getRiskIcon(assessment.risk_level) }}
          />
          <span className="risk-label" style={{ color: getRiskColor(assessment.risk_level) }}>
            {assessment.risk_level || 'Unknown'} Risk
          </span>
        </div>
        {onClose && typeof onClose === 'function' && assessment.risk_level && (
          <button className="close-btn" onClick={onClose}>&times;</button>
        )}
      </div>

      <div className="risk-details">
        {assessment.amount && (
          <div className="detail-row">
            <span className="label">Amount:</span>
            <span className="value">${assessment.amount.toLocaleString()}</span>
          </div>
        )}
        {assessment.beneficiary && (
          <div className="detail-row">
            <span className="label">Beneficiary:</span>
            <span className="value">{assessment.beneficiary}</span>
          </div>
        )}
        <div className="detail-row">
          <span className="label">Action:</span>
          <span className={`action-badge ${actionBadge.class}`}>
            {actionBadge.text}
          </span>
        </div>
        <div className="detail-row">
          <span className="label">Reason:</span>
          <span className="value">{assessment.reason || 'No reason provided'}</span>
        </div>
      </div>

      {assessment.risk_indicators && assessment.risk_indicators.length > 0 && (
        <div className="risk-indicators">
          <span className="label">Risk Indicators:</span>
          <ul>
            {assessment.risk_indicators.map((indicator, idx) => (
              <li key={idx}>{indicator}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default RiskPanel
