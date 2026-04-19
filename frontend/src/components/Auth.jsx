// src/components/Auth.jsx
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';

const colors = {
  deepDark: '#080616',
  navyBlue: '#1A1953',
  vibrantBlue: '#2F2FE4',
  textDim: '#A0A0C0'
};

const AuthForm = ({ type }) => {
  const navigate = useNavigate();
  const isLogin = type === 'login';

  const handleSubmit = (e) => {
    e.preventDefault();
    // Yahan baad mein login logic aayega
    navigate('/chat'); // Redirect to chat after "login"
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