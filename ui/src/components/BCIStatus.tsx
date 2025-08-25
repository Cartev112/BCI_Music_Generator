import React, { useState, useEffect } from 'react';
import { Brain } from 'lucide-react';

export function BCIStatus() {
  const [state, setState] = useState(0); // 0 = REST/idle, 1 = IMAGERY
  const [confidence, setConfidence] = useState(0.5); // probability value 0-1

  useEffect(() => {
    // Only set up electronAPI listeners if running in Electron context
    if (window.electronAPI && window.electronAPI.on) {
      // Listen for BCI state changes (0 = REST, 1 = IMAGERY)
      window.electronAPI.on('bci-state', (value) => {
        setState(Number(value) || 0);
      });

      // Listen for probability/confidence updates
      window.electronAPI.on('bci-prob', (value) => {
        const prob = Number(value) || 0.5;
        setConfidence(Math.max(0, Math.min(1, prob))); // clamp to 0-1
      });
    }
  }, []);

  const isImagery = state === 1;
  const stateLabel = isImagery ? 'IMAGERY' : 'IDLE';
  
  // Convert confidence to percentage for display
  const confidencePercent = Math.round(confidence * 100);
  
  return (
    <div style={panelStyle}>
      <div style={panelHeaderStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Brain width={16} height={16} />
          <span style={panelTitleStyle}>BCI Status</span>
        </div>
        <div style={panelMetaStyle}>real-time • neural</div>
      </div>
      
      <div style={{ padding: 16 }}>
        {/* State Display */}
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <div style={stateLabelStyle}>Current State</div>
          <div style={{
            ...stateValueStyle,
            color: isImagery ? '#10b981' : 'var(--muted)',
            textShadow: isImagery ? '0 0 8px #10b981' : 'none'
          }}>
            {stateLabel}
          </div>
        </div>

        {/* Confidence Display */}
        <div style={{ marginBottom: 12 }}>
          <div style={stateLabelStyle}>Confidence: {confidencePercent}%</div>
        </div>

        {/* Confidence Bar */}
        <div style={confidenceBarContainerStyle}>
          <div 
            style={{
              ...confidenceBarStyle,
              width: `${confidencePercent}%`,
              background: isImagery ? '#ffffff' : 'rgba(255, 255, 255, 0.6)',
              boxShadow: isImagery ? '0 0 8px rgba(255, 255, 255, 0.5)' : 'none'
            }}
          />
        </div>

        {/* Confidence Labels */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
          <span style={confidenceLabelStyle}>0%</span>
          <span style={confidenceLabelStyle}>50%</span>
          <span style={confidenceLabelStyle}>100%</span>
        </div>
      </div>
    </div>
  );
}

// Styles matching ControlRoom aesthetic
const panelStyle: React.CSSProperties = { 
  borderRadius: 12, 
  border: '1px solid var(--line)', 
  background: 'color-mix(in oklab, var(--panel) 90%, transparent)', 
  overflow: 'hidden' 
};

const panelHeaderStyle: React.CSSProperties = { 
  display: 'flex', 
  alignItems: 'center', 
  justifyContent: 'space-between', 
  padding: '12px 16px', 
  borderBottom: '1px solid var(--line)' 
};

const panelTitleStyle: React.CSSProperties = { 
  fontSize: 12, 
  letterSpacing: '0.16em', 
  textTransform: 'uppercase' 
};

const panelMetaStyle: React.CSSProperties = { 
  fontSize: 10, 
  color: 'var(--muted)', 
  letterSpacing: '0.2em', 
  textTransform: 'uppercase' 
};

const stateLabelStyle: React.CSSProperties = { 
  fontSize: 10, 
  letterSpacing: '0.2em', 
  textTransform: 'uppercase', 
  color: 'var(--muted)', 
  fontFamily: 'var(--font-mono)',
  marginBottom: 4
};

const stateValueStyle: React.CSSProperties = {
  fontSize: 24,
  fontWeight: 600,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  fontFamily: 'var(--font-mono)',
  transition: 'all 0.3s ease'
};

const confidenceBarContainerStyle: React.CSSProperties = {
  width: '100%',
  height: 8,
  background: 'var(--line)',
  borderRadius: 4,
  overflow: 'hidden',
  position: 'relative'
};

const confidenceBarStyle: React.CSSProperties = {
  height: '100%',
  borderRadius: 4,
  transition: 'all 0.3s ease',
  minWidth: 2
};

const confidenceLabelStyle: React.CSSProperties = {
  fontSize: 9,
  color: 'var(--muted)',
  fontFamily: 'var(--font-mono)',
  letterSpacing: '0.1em'
};

