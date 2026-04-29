// src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './LandingPage';
import ChatInterface from './ChatInterface';
import AuthForm from './components/Auth';
import VerifyOTP from './components/VerifyOtp';
import { AuthProvider } from './context/AuthContext'; // 1. AuthProvider Import karein
import ProtectedRoute from './components/ProtectedRoute'; // 2. ProtectedRoute Import karein
import './App.css';

function App() {
  return (
    <Router>
      {/* 3. AuthProvider ko yahan wrap karein taaki har route ko user data mil sake */}
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthForm type="login" />} />
          <Route path="/signup" element={<AuthForm type="signup" />} />
          <Route path="/verify-otp" element={<VerifyOTP />} />

          {/* 4. Protected Route - Sirf login users ke liye */}
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <ChatInterface />
              </ProtectedRoute>
            } 
          />

          {/* 404 Redirect */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;