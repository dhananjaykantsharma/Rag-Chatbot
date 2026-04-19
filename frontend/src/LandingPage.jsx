// src/LandingPage.jsx
import React from 'react';
import { Database, Zap, BrainCircuit, FileText, Search, ArrowRight, MessageSquareMore, Sparkles } from 'lucide-react';

// --- STYLES (Color Palette) ---
const colors = {
  deepDark: '#080616',    // Main Background
  navyBlue: '#1A1953',    // Cards / Secondary Background
  royalBlue: '#162E93',   // Primary Action / Highlights
  vibrantBlue: '#2F2FE4', // Accents / Glow Effects
  textWhite: '#FFFFFF',
  textDim: '#A0A0C0'
};

const styles = {
  section: {
    padding: '80px 10%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  glowEffect: {
    position: 'absolute',
    borderRadius: '50%',
    filter: 'blur(100px)',
    opacity: 0.2,
    zIndex: 0,
  },
  primaryBtn: {
    backgroundColor: colors.vibrantBlue,
    color: 'white',
    border: 'none',
    padding: '15px 30px',
    borderRadius: '30px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    transition: 'all 0.3s ease',
    boxShadow: `0 4px 20px rgba(47, 47, 228, 0.3)`,
    textDecoration: 'none', // For Link compatibility
  },
  card: {
    backgroundColor: colors.navyBlue,
    padding: '30px',
    borderRadius: '20px',
    border: `1px solid ${colors.vibrantBlue}22`, // Subtle vibrant blue border
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '15px',
    flex: '1 1 300px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
  }
};

const LandingPage = ({ onGetStarted }) => {

  // Primary Button Hover Effect Helper
  const handleBtnHover = (e, isHover) => {
    e.currentTarget.style.transform = isHover ? 'translateY(-3px)' : 'translateY(0)';
    e.currentTarget.style.boxShadow = isHover ? `0 8px 30px rgba(47, 47, 228, 0.5)` : `0 4px 20px rgba(47, 47, 228, 0.3)`;
  };

  // Card Hover Effect Helper
  const handleCardHover = (e, isHover) => {
    e.currentTarget.style.transform = isHover ? 'translateY(-5px)' : 'translateY(0)';
    e.currentTarget.style.boxShadow = isHover ? `0 10px 40px rgba(47, 47, 228, 0.2)` : '0 4px 15px rgba(0,0,0,0.3)';
    e.currentTarget.style.borderColor = isHover ? `${colors.vibrantBlue}66` : `${colors.vibrantBlue}22`;
  };

  return (
    <div style={{ backgroundColor: colors.deepDark, color: colors.textWhite, position: 'relative', overflow: 'hidden' }}>
      
      {/* Background Gradients/Glows */}
      <div style={{...styles.glowEffect, width: '400px', height: '400px', backgroundColor: colors.royalBlue, top: '-100px', left: '-100px'}}></div>
      <div style={{...styles.glowEffect, width: '500px', height: '500px', backgroundColor: colors.vibrantBlue, bottom: '-150px', right: '-150px'}}></div>

      {/* --- HEADER / NAV --- */}
      <header style={{ padding: '20px 10%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.navyBlue}`, zIndex: 10, position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '1.5rem', fontWeight: '700' }}>
            <div style={{ backgroundColor: colors.vibrantBlue, padding: '8px', borderRadius: '12px' }}><BrainCircuit size={24}/></div>
            RAG Insight AI
        </div>
        <button style={{...styles.primaryBtn, padding: '10px 20px', fontSize: '0.9rem'}} onMouseEnter={(e) => handleBtnHover(e, true)} onMouseLeave={(e) => handleBtnHover(e, false)} onClick={onGetStarted}>
            Launch Chat <ArrowRight size={18} />
        </button>
      </header>

      {/* --- HERO SECTION --- */}
      <section style={{...styles.section, paddingTop: '120px', paddingBottom: '100px', position: 'relative', zIndex: 1}}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: colors.navyBlue, padding: '8px 16px', borderRadius: '30px', color: colors.vibrantBlue, fontSize: '0.85rem', fontWeight: '500', border: `1px solid ${colors.vibrantBlue}44`, marginBottom: '20px' }}>
            <Sparkles size={16}/> Powered by Retrieval Augmented Generation (RAG)
        </div>
        <h1 style={{ fontSize: '3.5rem', fontWeight: '800', lineHeight: '1.1', margin: '0 0 25px 0', background: `linear-gradient(to right, ${colors.textWhite}, #D0D0F0)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Unlock Hidden Insights <br/> From Your Documents
        </h1>
        <p style={{ fontSize: '1.2rem', color: colors.textDim, maxWidth: '700px', lineHeight: '1.6', margin: '0 0 40px 0' }}>
            Stop wasting hours searching. RAG Insight AI analyze your documents (PDF, Text) instantly. Chat directly with your data and get accurate, context-aware answers.
        </p>
        <button style={{...styles.primaryBtn, fontSize: '1.1rem'}} onMouseEnter={(e) => handleBtnHover(e, true)} onMouseLeave={(e) => handleBtnHover(e, false)} onClick={onGetStarted}>
            Get Started Free <ArrowRight size={20} />
        </button>
      </section>

      {/* --- FEATURES SECTION --- */}
      <section style={{...styles.section, backgroundColor: `${colors.navyBlue}33`, position: 'relative', zIndex: 1}}>
        <h2 style={{ fontSize: '2.2rem', fontWeight: '700', margin: '0 0 60px 0' }}>Smart Intelligence for Smart Data</h2>
        <div style={{ display: 'flex', gap: '30px', flexWrap: 'wrap', width: '100%', maxWidth: '1200px', justifyContent: 'center' }}>
            
            {/* Feature 1 */}
            <div style={styles.card} onMouseEnter={(e) => handleCardHover(e, true)} onMouseLeave={(e) => handleCardHover(e, false)}>
                <div style={{ color: colors.vibrantBlue }}><FileText size={40}/></div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', margin: '10px 0' }}>Document Upload</h3>
                <p style={{ color: colors.textDim, fontSize: '0.9rem', margin: 0 }}>Easily upload PDF or TXT files. Our system indexes them automatically for instant access.</p>
            </div>

            {/* Feature 2 */}
            <div style={styles.card} onMouseEnter={(e) => handleCardHover(e, true)} onMouseLeave={(e) => handleCardHover(e, false)}>
                <div style={{ color: colors.vibrantBlue }}><Search size={40}/></div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', margin: '10px 0' }}>Semantic Search</h3>
                <p style={{ color: colors.textDim, fontSize: '0.9rem', margin: 0 }}>We don't just match keywords. We understand the *meaning* and *context* of your query for precise results.</p>
            </div>

            {/* Feature 3 */}
            <div style={styles.card} onMouseEnter={(e) => handleCardHover(e, true)} onMouseLeave={(e) => handleCardHover(e, false)}>
                <div style={{ color: colors.vibrantBlue }}><MessageSquareMore size={40}/></div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', margin: '10px 0' }}>Interactive Chat</h3>
                <p style={{ color: colors.textDim, fontSize: '0.9rem', margin: 0 }}>Ask questions naturally, summarize content, compare documents, and more through an intuitive chat interface.</p>
            </div>

            {/* Feature 4 */}
            <div style={styles.card} onMouseEnter={(e) => handleCardHover(e, true)} onMouseLeave={(e) => handleCardHover(e, false)}>
                <div style={{ color: colors.vibrantBlue }}><BrainCircuit size={40}/></div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: '600', margin: '10px 0' }}>Context-Aware AI</h3>
                <p style={{ color: colors.textDim, fontSize: '0.9rem', margin: 0 }}>Powered by advanced LLMs that use *your uploaded data* to generate accurate, source-backed answers.</p>
            </div>
        </div>
      </section>

      {/* --- HOW IT WORKS --- */}
      <section style={{...styles.section, paddingBottom: '120px'}}>
        <h2 style={{ fontSize: '2.2rem', fontWeight: '700', margin: '0 0 60px 0' }}>Simple 3-Step Process</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '30px', width: '100%', maxWidth: '900px', color: colors.textDim }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: 60, height: 60, borderRadius: '50%', border: `2px solid ${colors.vibrantBlue}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: '700', color: colors.vibrantBlue }}>1</div>
                Upload your files
            </div>
            <ArrowRight size={24}/>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: 60, height: 60, borderRadius: '50%', border: `2px solid ${colors.vibrantBlue}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: '700', color: colors.vibrantBlue }}>2</div>
                AI indexes the content
            </div>
            <ArrowRight size={24}/>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: 60, height: 60, borderRadius: '50%', border: `2px solid ${colors.vibrantBlue}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: '700', color: colors.vibrantBlue }}>3</div>
                Start chatting
            </div>
        </div>
      </section>

      {/* --- CTA SECTION --- */}
      <section style={{...styles.section, backgroundColor: colors.royalBlue, borderTop: `1px solid ${colors.vibrantBlue}44`, position: 'relative', overflow: 'hidden'}}>
         <div style={{...styles.glowEffect, width: '300px', height: '300px', backgroundColor: colors.vibrantBlue, top: '-50px', left: '-50px', opacity: 0.4}}></div>
         <h2 style={{ fontSize: '2.5rem', fontWeight: '800', margin: '0 0 20px 0', zIndex: 1, position: 'relative' }}>Ready to chat with your documents?</h2>
         <p style={{ fontSize: '1.1rem', color: '#D0D0F0', maxWidth: '600px', margin: '0 0 40px 0', zIndex: 1, position: 'relative' }}>
            Try RAG Insight AI now and see how quickly you can find the information you need. No training required.
         </p>
         <button style={{...styles.primaryBtn, backgroundColor: colors.deepDark, color: colors.vibrantBlue, border: `2px solid ${colors.vibrantBlue}`, zIndex: 1, position: 'relative' }} onMouseEnter={(e) => handleBtnHover(e, true)} onMouseLeave={(e) => handleBtnHover(e, false)} onClick={onGetStarted}>
            Launch Chat App <ArrowRight size={20} />
        </button>
      </section>

      {/* --- FOOTER --- */}
      <footer style={{ padding: '30px 10%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem', color: colors.textDim, borderTop: `1px solid ${colors.navyBlue}` }}>
        <div>&copy; {new Date().getFullYear()} RAG Insight AI. All rights reserved.</div>
        <div style={{ display: 'flex', gap: '20px' }}>
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
            <span>Contact</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;