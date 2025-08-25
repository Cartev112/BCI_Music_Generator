import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material';

export function HomePage() {
  const navigate = useNavigate();
  const theme = useTheme();
  
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: theme.palette.background.default, 
      color: theme.palette.text.primary, 
      fontFamily: 'IBM Plex Mono, monospace', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center' 
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');
      `}</style>
      <div style={{ 
        border: `1px solid ${theme.palette.divider}`, 
        background: theme.palette.background.paper, 
        borderRadius: 16, 
        padding: 32, 
        width: 'min(720px, 92vw)', 
        textAlign: 'center' 
      }}>
        <h1 style={{ 
          fontSize: 48, 
          margin: 0, 
          letterSpacing: '0.18em', 
          textTransform: 'uppercase',
          color: theme.palette.text.primary
        }}>Brain Jazz</h1>
        <div style={{ marginTop: 24, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/setup')} style={{...baseBtn, background: theme.palette.text.primary, color: theme.palette.background.default, border: `1px solid ${theme.palette.text.primary}`}}>New Session</button>
          <button onClick={() => navigate('/history')} style={{...baseBtn, background: 'transparent', color: theme.palette.text.primary, border: `1px solid ${theme.palette.divider}`}}>Session History</button>
          <button onClick={() => navigate('/settings')} style={{...baseBtn, background: 'transparent', color: theme.palette.text.primary, border: `1px solid ${theme.palette.divider}`}}>Settings</button>
        </div>
      </div>
    </div>
  );
}

const baseBtn: React.CSSProperties = { 
  fontFamily: 'IBM Plex Mono, monospace', 
  letterSpacing: '0.12em', 
  textTransform: 'uppercase', 
  padding: '12px 18px', 
  borderRadius: 10, 
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 600
};



