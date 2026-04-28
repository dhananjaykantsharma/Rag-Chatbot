import React, { useState, useRef, useEffect } from 'react';
import { Bot, User, Send, Sparkles, Database, X, Upload, FileText } from 'lucide-react';

const colors = {
  deepDark: '#080616',    // Main Background
  navyBlue: '#1A1953',    // Chat Bubbles / Header
  royalBlue: '#162E93',   // Primary / User Bubbles
  vibrantBlue: '#2F2FE4', // Accents / Highlights
  textWhite: '#FFFFFF',
  textDim: '#A0A0C0'
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { text: "Hello! Main aapka RAG assistant hoon. Mere paas documents ka context hai. Aap mujhse kuch bhi puch sakte hain!", isUser: false },
    { text: "Hello! Kya aap mujhe PDF ke basis par summary de sakte hain?", isUser: true },
    { text: "Ji bilkul! Aap apna sawal puchiye, main context check karke bataunga.", isUser: false },
  ]);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const [showModal, setShowModal] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Abhi ke liye bas local state update (No API call)
    setMessages([...messages, { text: input, isUser: true }]);
    setInput("");
  };

  return (
    <div style={{
      backgroundColor: colors.deepDark,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      color: colors.textWhite,
      fontFamily: 'Inter, sans-serif'
    }}>

      {showModal && (
        <div style={styles.overlay}>
          <div style={styles.modalCard}>
            {/* Header */}
            <div style={styles.modalHeader}>
              <h3>Upload Data Source</h3>
              <X style={{ cursor: 'pointer' }} onClick={() => setShowModal(false)} />
            </div>

            {/* Upload Area */}
            <div style={styles.uploadBox}>
              <input
                type="file"
                id="fileInput"
                hidden
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
              <label htmlFor="fileInput" style={styles.label}>
                <Upload size={40} color={colors.vibrantBlue} />
                <p>{selectedFile ? selectedFile.name : "Choose a PDF or TXT file"}</p>
              </label>
            </div>

            {/* Action Button */}
            <button
              style={styles.uploadBtn}
              onClick={() => {
                // Yahan aap handleFileUpload function call karenge
                setShowModal(false);
              }}
            >
              Start Processing
            </button>
          </div>
        </div>
      )}

      {/* --- HEADER --- */}
      <header style={{
        padding: '20px 40px',
        backgroundColor: colors.navyBlue,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: `2px solid ${colors.vibrantBlue}`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ backgroundColor: colors.vibrantBlue, padding: '8px', borderRadius: '12px' }}>
            <Database size={24} />
          </div>
          <h2 style={{ margin: 0, fontSize: '1.4rem' }}>RAG Insight AI</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>

          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: colors.vibrantBlue,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            border: `2px solid rgba(255,255,255,0.1)`,
            fontWeight: 'bold',
            color: 'white',
            fontSize: '1.2rem',
            boxShadow: '0 0 10px rgba(47, 47, 228, 0.4)'
          }}>
            D
          </div>
        </div>
      </header>

      {/* --- CHAT AREA --- */}
      <main ref={scrollRef} style={{
        flex: 1,
        overflowY: 'auto',
        padding: '30px 20%',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        backgroundImage: `radial-gradient(circle at top right, ${colors.navyBlue}, transparent)`
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: 'flex',
            justifyContent: msg.isUser ? 'flex-end' : 'flex-start',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            {!msg.isUser && <div style={avatarStyle}><Bot size={18} /></div>}

            <div style={{
              maxWidth: '75%',
              padding: '12px 18px',
              borderRadius: msg.isUser ? '20px 20px 4px 20px' : '4px 20px 20px 20px',
              backgroundColor: msg.isUser ? colors.royalBlue : colors.navyBlue,
              border: `1px solid ${colors.vibrantBlue}44`,
              boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
              fontSize: '0.95rem',
              lineHeight: '1.5'
            }}>
              {msg.text}
            </div>

            {msg.isUser && <div style={{ ...avatarStyle, backgroundColor: colors.vibrantBlue }}><User size={18} /></div>}
          </div>
        ))}
      </main>

      {/* --- INPUT AREA --- */}
      <footer style={{
        padding: '30px 20%',
        background: `linear-gradient(to top, ${colors.deepDark}, transparent)`
      }}>
        <form onSubmit={handleSendMessage} style={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center'
        }}>
          <input
            type="text"
            placeholder="Apne documents ke baare mein puchiye..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{
              width: '100%',
              padding: '16px 60px 16px 25px',
              borderRadius: '30px',
              border: `2px solid ${colors.navyBlue}`,
              backgroundColor: 'rgba(26, 25, 83, 0.3)',
              color: 'white',
              fontSize: '1rem',
              outline: 'none',
              transition: 'all 0.3s ease',
            }}
            onFocus={(e) => e.target.style.borderColor = colors.vibrantBlue}
            onBlur={(e) => e.target.style.borderColor = colors.navyBlue}
          />
          <button type="submit" style={{
            position: 'absolute',
            right: '10px',
            backgroundColor: colors.vibrantBlue,
            border: 'none',
            borderRadius: '50%',
            width: '45px',
            height: '45px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            transition: 'transform 0.2s'
          }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <Send size={20} />
          </button>
        </form>
        <p style={{ textAlign: 'center', color: colors.textDim, fontSize: '0.75rem', marginTop: '10px' }}>
          <Sparkles size={12} style={{ marginRight: '5px' }} />
          AI responses are generated based on provided document context.
        </p>
      </footer>
    </div>
  );
};

const avatarStyle = {
  width: '36px',
  height: '36px',
  borderRadius: '10px',
  backgroundColor: colors.navyBlue,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  border: `1px solid ${colors.vibrantBlue}66`
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.85)', // Dark transparent background
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2000,
    backdropFilter: 'blur(5px)', // Premium blur effect
  },
  modalCard: {
    backgroundColor: colors.navyBlue,
    padding: '30px',
    borderRadius: '20px',
    width: '400px',
    border: `1px solid ${colors.vibrantBlue}66`,
    textAlign: 'center',
  },
  uploadBox: {
    border: `2px dashed ${colors.vibrantBlue}44`,
    borderRadius: '15px',
    padding: '40px 20px',
    margin: '20px 0',
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  uploadBtn: {
    width: '100%',
    padding: '12px',
    backgroundColor: colors.vibrantBlue,
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontWeight: 'bold',
    cursor: 'pointer',
  }
};

export default ChatInterface;