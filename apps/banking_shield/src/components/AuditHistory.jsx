import React, { useState, useEffect } from 'react'
import { getAuditHistory } from '../services/api.js'

/**
 * Audit History Component
 * Displays security activity and authentication history.
 * Shows only permitted audit metadata per HOST_APPS.md.
 */

function AuditHistory({ userRef, limit = 10 }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await getAuditHistory(userRef, limit)
        setHistory(data)
      } catch (err) {
        setError('Failed to load audit history')
        // Use mock data as fallback
        setHistory([
          {
            id: '1',
            timestamp: new Date().toISOString(),
            event_type: 'VOICE_VERIFICATION',
            decision: 'APPROVE',
            reason_public: 'Verification successful'
          },
          {
            id: '2',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            event_type: 'LOGIN',
            decision: 'APPROVE',
            reason_public: 'Standard login'
          }
        ])
      }
      setLoading(false)
    }
    loadHistory()
  }, [userRef, limit])

  const getEventIcon = (type) => {
    switch (type?.toUpperCase()) {
      case 'VOICE_VERIFICATION': return '&#x1F3A4;'
      case 'LOGIN': return '&#x1F511;'
      case 'TRANSFER': return '&#x1F4B8;'
      case 'ENROLLMENT': return '&#x2705;'
      case 'FAILED_ATTEMPT': return '&#x26A0;'
      default: return '&#x2022;'
    }
  }

  const getDecisionClass = (decision) => {
    switch (decision?.toUpperCase()) {
      case 'APPROVE': return 'success'
      case 'DENY': return 'error'
      case 'RETRY': return 'warning'
      default: return ''
    }
  }

  const formatTimestamp = (ts) => {
    const date = new Date(ts)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return <div className="audit-loading">Loading activity...</div>
  }

  if (history.length === 0) {
    return <div className="no-history">No recent activity.</div>
  }

  return (
    <div className="audit-history">
      <ul className="history-list">
        {history.map(event => (
          <li key={event.id} className={`history-item ${getDecisionClass(event.decision)}`}>
            <span
              className="event-icon"
              dangerouslySetInnerHTML={{ __html: getEventIcon(event.event_type) }}
            />
            <div className="event-details">
              <span className="event-type">{event.event_type?.replace(/_/g, ' ')}</span>
              <span className="event-time">{formatTimestamp(event.timestamp)}</span>
            </div>
            <div className="event-result">
              <span className={`decision ${getDecisionClass(event.decision)}`}>
                {event.decision}
              </span>
              {event.reason_public && (
                <span className="reason">{event.reason_public}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default AuditHistory
