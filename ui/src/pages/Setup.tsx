import React from 'react';
import { useNavigate } from 'react-router-dom';

export function SetupPage() {
  const navigate = useNavigate();
  const [status, setStatus] = React.useState({ board: false, classifier: false, osc: false });
  const [prob, setProb] = React.useState(0);

  React.useEffect(() => {
    // Only set up electronAPI listeners if running in Electron context
    if (window.electronAPI && window.electronAPI.onStatus && window.electronAPI.on) {
      window.electronAPI.onStatus('board', (v) => setStatus((s) => ({ ...s, board: v })));
      window.electronAPI.onStatus('classifier', (v) => setStatus((s) => ({ ...s, classifier: v })));
      window.electronAPI.onStatus('osc', (v) => setStatus((s) => ({ ...s, osc: v })));
      window.electronAPI.on('bci-prob', (v) => setProb(Number(v) || 0));
    }
  }, []);

  const allGood = status.board && status.classifier && status.osc;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');`}</style>
      <div style={{ maxWidth: 960, margin: '0 auto', padding: 16 }}>
        <h2 style={{ letterSpacing: '0.18em', textTransform: 'uppercase', marginBottom: 12 }}>Headset Setup</h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div style={panelStyle}>
            <div style={panelHeaderStyle}>
              <span style={panelTitleStyle}>Connection Status</span>
            </div>
            <div style={{ padding: 16, display: 'grid', gap: 8 }}>
              {[
                { label: 'Board Connected', on: status.board },
                { label: 'Classifier Ready', on: status.classifier },
                { label: 'OSC Link', on: status.osc },
              ].map((it) => (
                <div key={it.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={kpiLabelStyle}>{it.label}</span>
                  <span style={{ width: 12, height: 12, borderRadius: 12, background: it.on ? '#10b981' : '#374151', boxShadow: it.on ? '0 0 10px #10b981' : 'none' }} />
                </div>
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <div style={panelHeaderStyle}>
              <span style={panelTitleStyle}>Quick Tips</span>
            </div>
            <div style={{ padding: 16, color: 'var(--muted)' }}>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                <li>Ensure electrodes have good contact; tighten straps if needed.</li>
                <li>Minimize movement and blinking during calibration.</li>
                <li>Verify sample activity appears shortly after start.</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 12 }}>
          <div style={panelStyle}>
            <div style={panelHeaderStyle}>
              <span style={panelTitleStyle}>Live Check</span>
            </div>
            <div style={{ padding: 16 }}>
              <div>Probability feed {prob > 0 ? 'active' : 'idle'} ({prob.toFixed(2)})</div>
              <div style={{ color: allGood ? '#10b981' : '#f59e0b', marginTop: 6 }}>
                {allGood ? 'All systems ready.' : 'Waiting for all systems to be ready...'}
              </div>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 6 }}>
                Tip: Use Dev Bypass to preview the session UI without hardware.
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
          <button onClick={() => navigate('/')} style={btnOutline}>Back</button>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => navigate('/control')} style={btnOutline}>Dev Bypass</button>
            <button onClick={() => navigate('/control')} disabled={!allGood} style={{ ...btnPrimary, opacity: allGood ? 1 : 0.5 }}>Continue</button>
          </div>
        </div>
      </div>
    </div>
  );
}

const baseBtn: React.CSSProperties = { fontFamily: 'var(--font-mono)', letterSpacing: '0.12em', textTransform: 'uppercase', padding: '10px 16px', borderRadius: 10, cursor: 'pointer' };
const btnPrimary: React.CSSProperties = { ...baseBtn, background: 'var(--text)', color: 'var(--bg)', border: '1px solid var(--text)' };
const btnOutline: React.CSSProperties = { ...baseBtn, background: 'transparent', color: 'var(--text)', border: '1px solid var(--line)' };

// Shared panel styles (match ControlRoom)
const panelStyle: React.CSSProperties = {
  borderRadius: 12,
  border: '1px solid var(--line)',
  background: 'color-mix(in oklab, var(--panel) 90%, transparent)',
  overflow: 'hidden',
};
const panelHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '12px 16px',
  borderBottom: '1px solid var(--line)',
};
const panelTitleStyle: React.CSSProperties = {
  fontSize: 12,
  letterSpacing: '0.16em',
  textTransform: 'uppercase',
};
const kpiLabelStyle: React.CSSProperties = {
  fontSize: 10,
  letterSpacing: '0.2em',
  textTransform: 'uppercase',
  color: 'var(--muted)',
};


