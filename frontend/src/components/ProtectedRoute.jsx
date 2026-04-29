// src/components/ProtectedRoute.jsx
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext'; // Path ko '../context/AuthContext' kiya gaya hai

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  // Jab tak API check kar rahi hai, ye dikhega
  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        backgroundColor: '#080616', 
        color: 'white' 
      }}>
        Loading user status...
      </div>
    );
  }

  // Agar user login nahi hai, toh login page par bhej do
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Agar user login hai, toh actual component (ChatInterface) dikhao
  return children;
};

export default ProtectedRoute; // Ye line error fix karegi (export default missing tha)