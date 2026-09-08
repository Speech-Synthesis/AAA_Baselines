import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { RegisterPage } from './components/RegisterPage';
import { EnrollPage } from './components/EnrollPage';
import { LoginPage } from './components/LoginPage';
import { VerifyPage } from './components/VerifyPage';
import { DashboardPage } from './components/DashboardPage';
import { checkServerHealth, getMockStore } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('register');
  const [isServerLive, setIsServerLive] = useState(false);
  
  // Default mock initial user
  const initialUsers = getMockStore().users;
  const [registeredUsers, setRegisteredUsers] = useState(initialUsers);
  const [activeUser, setActiveUser] = useState(initialUsers[0]);

  useEffect(() => {
    // Check server availability on mount
    checkServerHealth().then(setIsServerLive);
  }, []);

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeUser={activeUser}
        isServerLive={isServerLive}
      />

      <main>
        {activeTab === 'register' && (
          <RegisterPage
            activeUser={activeUser}
            setActiveUser={setActiveUser}
            registeredUsers={registeredUsers}
            setRegisteredUsers={setRegisteredUsers}
            onComplete={() => setActiveTab('enroll')}
          />
        )}

        {activeTab === 'enroll' && (
          <EnrollPage
            activeUser={activeUser}
            onComplete={() => setActiveTab('verify')}
          />
        )}

        {activeTab === 'login' && (
          <LoginPage
            activeUser={activeUser}
            setActiveUser={setActiveUser}
            registeredUsers={registeredUsers}
            onSelectUser={() => setActiveTab('verify')}
          />
        )}

        {activeTab === 'verify' && (
          <VerifyPage activeUser={activeUser} />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage activeUser={activeUser} />
        )}
      </main>
    </div>
  );
}

export default App;
