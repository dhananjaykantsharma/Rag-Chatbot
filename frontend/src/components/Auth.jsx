// src/components/Auth.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';
import api from '../api';
import { useAuth } from '../context/AuthContext'; // useAuth hook se checkAuth access karein

const colors = {
  deepDark: '#080616',
  navyBlue: '#1A1953',
  vibrantBlue: '#2F2FE4',
  textDim: '#A0A0C0'
};


const AuthForm = ({ type }) => {
  const navigate = useNavigate();
  const isLogin = type === 'login';
  const [error, setError] = useState("");
  const { checkAuth } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const endpoint = isLogin ? '/auth/login' : '/auth/signup';

    try {
      let response;

      if (isLogin) {
        // 1. Login ke liye Form Data banana zaroori hai (FastAPI OAuth2 requirement)
        const formData = new URLSearchParams();
        formData.append('username', e.target[0].value); // Email field
        formData.append('password', e.target[1].value); // Password field

        response = await api.post(endpoint, formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });
      } else {
        // 2. Signup ke liye normal JSON payload
        const signupPayload = {
          full_name: e.target[0].value,
          email: e.target[1].value,
          password: e.target[2].value
        };
        response = await api.post(endpoint, signupPayload);
      }

      // 3. Response handling
      if (response.status === 200) {
        if (!isLogin) {
          localStorage.setItem('userEmail', e.target[1].value);
          navigate('/verify-otp');
        } else {
          // Token save karein (Backend se 'access_token' aur 'token_type' aata hai)
          localStorage.setItem('token', response.data.access_token);
          await checkAuth();
          navigate('/chat');
        }
      }
    } catch (err) {
      // Backend se aane wala error message display karein
      const errorMsg = err.response?.data?.detail || "An error occurred. Please try again.";
      setError(errorMsg);
      console.error("Auth Error:", err.response?.data);
    }
  };

  return (
    <div style={authStyles.container}>
      <div style={authStyles.card}>
        <h2 style={{ fontSize: '2rem', marginBottom: '10px' }}>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
        <p style={{ color: colors.textDim, marginBottom: '30px' }}>
          {isLogin ? 'Login to access your documents.' : 'Start analyzing your data today.'}
        </p>

        <form onSubmit={handleSubmit} style={authStyles.form}>
          {!isLogin && (
            <div style={authStyles.inputGroup}>
              <User size={20} style={authStyles.icon} />
              <input type="text" placeholder="Full Name" style={authStyles.input} required />
            </div>
          )}
          <div style={authStyles.inputGroup}>
            <Mail size={20} style={authStyles.icon} />
            <input type="email" placeholder="Email Address" style={authStyles.input} required />
          </div>
          <div style={authStyles.inputGroup}>
            <Lock size={20} style={authStyles.icon} />
            <input type="password" placeholder="Password" style={authStyles.input} required />
          </div>

          <button type="submit" style={authStyles.button}>
            {isLogin ? 'Login' : 'Sign Up'} <ArrowRight size={20} />
          </button>
        </form>

        <p style={{ marginTop: '20px', color: colors.textDim }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <Link to={isLogin ? '/signup' : '/login'} style={{ color: colors.vibrantBlue, textDecoration: 'none', fontWeight: 'bold' }}>
            {isLogin ? 'Sign Up' : 'Login'}
          </Link>
        </p>
      </div>
    </div>
  );
};

const authStyles = {
  container: {
    height: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.deepDark,
    backgroundImage: `radial-gradient(circle at center, ${colors.navyBlue}33 0%, ${colors.deepDark} 100%)`,
  },
  card: {
    backgroundColor: colors.navyBlue,
    padding: '40px',
    borderRadius: '24px',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'center',
    border: `1px solid ${colors.vibrantBlue}33`,
    boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
  },
  form: { display: 'flex', flexDirection: 'column', gap: '20px' },
  inputGroup: { position: 'relative', display: 'flex', alignItems: 'center' },
  icon: { position: 'absolute', left: '15px', color: colors.vibrantBlue },
  input: {
    width: '100%',
    padding: '12px 15px 12px 45px',
    borderRadius: '12px',
    border: 'none',
    backgroundColor: 'rgba(8, 6, 22, 0.5)',
    color: 'white',
    outline: 'none',
    fontSize: '1rem',
  },
  button: {
    backgroundColor: colors.vibrantBlue,
    color: 'white',
    border: 'none',
    padding: '14px',
    borderRadius: '12px',
    fontSize: '1rem',
    fontWeight: 'bold',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '10px',
    marginTop: '10px'
  }
};

export default AuthForm;