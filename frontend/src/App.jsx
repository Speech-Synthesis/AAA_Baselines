import React, { useState, useEffect } from 'react';
import { Sidebar, HeaderStepper } from './components/Navbar';
import { RegisterPage } from './components/RegisterPage';
import { EnrollPage } from './components/EnrollPage';
import { LoginPage } from './components/LoginPage';
import { VerifyPage } from './components/VerifyPage';
import { DashboardPage } from './components/DashboardPage';
import { checkServerHealth, getAllUsers } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('register');
  const [isServerLive, setIsServerLive] = useState(false);

  const [registeredUsers, setRegisteredUsers] = useState([]);
  const [activeUser, setActiveUser] = useState(null);

  // Load users from database on startup
  const loadUsers = async () => {
    const users = await getAllUsers();
    setRegisteredUsers(users);
    if (users.length > 0 && !activeUser) {
      setActiveUser(users[0]);
    }
  };

  useEffect(() => {
    checkServerHealth().then(setIsServerLive);
    loadUsers();
  }, []);

  return (
    <div className="saas-layout">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeUser={activeUser}
        isServerLive={isServerLive}
      />

      {/* Main Process Flow Content Area */}
      <main className="saas-main-content">
        {/* Header Process Flow Stepper */}
        <HeaderStepper
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        {/* Step 1: Register */}
        {activeTab === 'register' && (
          <RegisterPage
            activeUser={activeUser}
            setActiveUser={setActiveUser}
            registeredUsers={registeredUsers}
            setRegisteredUsers={setRegisteredUsers}
            refreshUsers={loadUsers}
            onComplete={() => setActiveTab('enroll')}
          />
        )}

        {/* Step 2: Enroll */}
        {activeTab === 'enroll' && (
          <EnrollPage
            activeUser={activeUser}
            onComplete={() => setActiveTab('verify')}
          />
        )}

        {/* Step 3: Authenticate */}
        {activeTab === 'verify' && (
          <VerifyPage
            activeUser={activeUser}
            onComplete={() => setActiveTab('dashboard')}
          />
        )}

        {/* Step 4: Audit & Analytics */}
        {activeTab === 'dashboard' && (
          <DashboardPage activeUser={activeUser} />
        )}

        {/* Advanced Step: Switch User */}
        {activeTab === 'login' && (
          <LoginPage
            activeUser={activeUser}
            setActiveUser={setActiveUser}
            registeredUsers={registeredUsers}
            onSelectUser={() => setActiveTab('verify')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
