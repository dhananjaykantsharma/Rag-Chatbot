import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, ArrowRight, RefreshCw } from 'lucide-react';
import api from '../api'; // Your axios instance

const colors = {
  deepDark: '#080616',
  navyBlue: '#1A1953',
  vibrantBlue: '#2F2FE4',
  textDim: '#A0A0C0'
};

const VerifyOTP = () => {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get email from previous signup/login state if available
  const email = localStorage.getItem('userEmail');

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
        if (!email) {
          setError("Email not found. Please go back and try again.");
          setLoading(false);
          return;
        }
      const response = await api.post('/auth/verify-otp',{}, {
        params:{
            email: email,
            otp: otp
        }
      });
      
      // If verification is successful
      alert("Email verified successfully!");
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.iconCircle}>
          <ShieldCheck size={40} color={colors.vibrantBlue} />
        </div>
        
        <h2 style={{ fontSize: '2rem', marginBottom: '10px' }}>Verify Email</h2>
        <p style={{ color: colors.textDim, marginBottom: '30px', lineHeight: '1.5' }}>
          We've sent a 6-digit code to <br />
          <span style={{ color: 'white', fontWeight: 'bold' }}>{email}</span>
        </p>

        {error && <p style={styles.errorText}>{error}</p>}

        <form onSubmit={handleVerify} style={styles.form}>
          <div style={styles.inputGroup}>
            <input 
              type="text" 
              placeholder="0 0 0 0 0 0" 
              maxLength="6"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              style={styles.otpInput} 
              required 
            />
          </div>

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Verifying...' : 'Verify Account'} 
            {!loading && <ArrowRight size={20} />}
          </button>
        </form>

        <div style={{ marginTop: '25px' }}>
          <p style={{ color: colors.textDim }}>
            Didn't receive the code?
          </p>
          <button style={styles.resendBtn} onClick={() => alert("OTP Resent!")}>
            <RefreshCw size={14} /> Resend Code
          </button>
        </div>
      </div>
    </div>
  );
};

const styles = {
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
  iconCircle: {
    width: '80px',
    height: '80px',
    backgroundColor: 'rgba(47, 47, 228, 0.1)',
    borderRadius: '50%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    margin: '0 auto 20px auto',
  },
  form: { display: 'flex', flexDirection: 'column', gap: '20px' },
  otpInput: {
    width: '100%',
    padding: '15px',
    borderRadius: '12px',
    border: `2px solid ${colors.vibrantBlue}33`,
    backgroundColor: 'rgba(8, 6, 22, 0.5)',
    color: 'white',
    outline: 'none',
    fontSize: '1.5rem',
    textAlign: 'center',
    letterSpacing: '8px',
    fontWeight: 'bold',
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
  },
  resendBtn: {
    background: 'none',
    border: 'none',
    color: colors.vibrantBlue,
    cursor: 'pointer',
    fontWeight: 'bold',
    marginTop: '5px',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px'
  },
  errorText: {
    color: '#ff4d4d',
    marginBottom: '15px',
    fontSize: '0.9rem'
  }
};

export default VerifyOTP;