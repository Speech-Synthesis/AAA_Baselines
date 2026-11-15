import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Transactions from './pages/Transactions.jsx'
import Enrollment from './pages/Enrollment.jsx'
import Verification from './pages/Verification.jsx'
import { checkAAAHealth } from './services/api.js'

/**
 * Banking Shield - AAA Voice Authentication Demo
 *
 * Host App 1 as specified in HOST_APPS.md
 * Tenant: bank_demo
 *
 * Features:
 * - Mock login with seeded accounts
 * - Transaction simulation (view balance, transfers, beneficiaries)
 * - Risk-based step-up authentication
 * - Voice enrollment via AAA capture
 * - Voice authentication for high-risk actions
 * - Fraud/security dashboard
 * - Audit history
 */

function App() {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [backendStatus, setBackendStatus] = useState({ connected: false, checking: true })

  // Check backend connectivity on mount
  useEffect(() => {
    async function checkBackend() {
      try {
        const health = await checkAAAHealth()
        setBackendStatus({
          connected: true,
          checking: false,
          status: health.status || 'HEALTHY',
          mock: health._mock || false,
        })
      } catch (err) {
        console.warn('[Banking Shield] Backend not available:', err.message)
        setBackendStatus({
          connected: false,
          checking: false,
          error: err.message,
        })
      }
    }
    checkBackend()
    const interval = setInterval(checkBackend, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setUser(null)
    setIsAuthenticated(false)
  }

  return (
    <BrowserRouter>
      <div className="app-container">
        {/* Backend Status Bar */}
        <div className="backend-status-bar" style={{
          background: backendStatus.connected
            ? (backendStatus.mock ? '#f59e0b' : '#10b981')
            : '#ef4444',
          color: 'white',
          padding: '4px 12px',
          fontSize: '12px',
          textAlign: 'center',
          fontWeight: '500'
        }}>
          {backendStatus.checking ? '⏳ Connecting to AAA Engine...' :
           backendStatus.connected ? (
             backendStatus.mock
               ? '🔗 MOCK API MODE — Demo Only'
               : '🟢 LIVE BACKEND — Connected to AAA Engine'
           ) : '🔴 OFFLINE — AAA Backend Unavailable'}
          <span style={{ marginLeft: '12px', opacity: 0.8 }}>
            Tenant: bank_demo
          </span>
        </div>
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ?
                <Navigate to="/dashboard" replace /> :
                <Login onLogin={handleLogin} />
            }
          />
          <Route
            path="/dashboard"
            element={
              isAuthenticated ?
                <Dashboard user={user} onLogout={handleLogout} /> :
                <Navigate to="/login" replace />
            }
          />
          <Route
            path="/transactions"
            element={
              isAuthenticated ?
                <Transactions user={user} onLogout={handleLogout} /> :
                <Navigate to="/login" replace />
            }
          />
          <Route
            path="/enrollment"
            element={
              isAuthenticated ?
                <Enrollment user={user} onLogout={handleLogout} /> :
                <Navigate to="/login" replace />
            }
          />
          <Route
            path="/verify"
            element={
              isAuthenticated ?
                <Verification user={user} onLogout={handleLogout} /> :
                <Navigate to="/login" replace />
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
