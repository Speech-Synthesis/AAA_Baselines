import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Transactions from './pages/Transactions.jsx'
import Enrollment from './pages/Enrollment.jsx'
import Verification from './pages/Verification.jsx'

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
