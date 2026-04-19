// src/App.js
import React, { useState } from 'react';
import LandingPage from './LandingPage';
import ChatInterface from './ChatInterface'; // Jo aapne pehle banaya tha
import './App.css'; // Global font settings (Inter) must be here

function App() {
  // Navigation State
  const [showChat, setShowChat] = useState(false);

  return (
    <div className="App">
      {showChat ? (
        // Show Chat Interface
        <ChatInterface />
      ) : (
        // Show Landing Page first
        <LandingPage onGetStarted={() => setShowChat(true)} />
      )}
    </div>
  );
}

export default App;