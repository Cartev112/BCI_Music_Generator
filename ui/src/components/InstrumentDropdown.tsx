import React, { useState } from 'react';
import { Music } from 'lucide-react';

export function InstrumentDropdown() {
  const [selectedInstrument, setSelectedInstrument] = useState('piano');

  const instruments = [
    { value: 'piano', label: 'Piano' },
    { value: 'electric_piano', label: 'Electric Piano' },
    { value: 'organ', label: 'Organ' },
    { value: 'guitar', label: 'Guitar' },
    { value: 'bass', label: 'Bass' },
    { value: 'strings', label: 'Strings' },
    { value: 'pad', label: 'Pad' },
    { value: 'lead', label: 'Lead' },
    { value: 'bells', label: 'Bells' },
    { value: 'choir', label: 'Choir' }
  ];

  function handleInstrumentChange(value: string) {
    setSelectedInstrument(value);
    // Send to backend when electronAPI is available
    if (window.electronAPI && window.electronAPI.sendOSC) {
      window.electronAPI.sendOSC('music-instrument', value);
    }
  }

  return (
    <div style={panelStyle}>
      <div style={panelHeaderStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Music width={16} height={16} />
          <span style={panelTitleStyle}>Instrument</span>
        </div>
        <div style={panelMetaStyle}>sound • timbre</div>
      </div>
      <div style={{ padding: 16 }}>
        <div style={controlLabelStyle}>Sound Source</div>
        <div style={{ position: 'relative', marginTop: 8 }}>
          <select
            value={selectedInstrument}
            onChange={(e) => handleInstrumentChange(e.target.value)}
            style={dropdownStyle}
          >
            {instruments.map((instrument) => (
              <option key={instrument.value} value={instrument.value}>
                {instrument.label}
              </option>
            ))}
          </select>
          <div style={dropdownArrowStyle}>▼</div>
        </div>
        
        {/* Instrument categories */}
        <div style={{ marginTop: 16 }}>
          <div style={controlLabelStyle}>Quick Select</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 8 }}>
            {[
              { category: 'Keys', instruments: ['piano', 'electric_piano', 'organ'] },
              { category: 'Strings', instruments: ['guitar', 'bass', 'strings'] },
              { category: 'Synth', instruments: ['pad', 'lead'] },
              { category: 'Melodic', instruments: ['bells', 'choir'] }
            ].map((group) => (
              <div key={group.category}>
                <div style={categoryLabelStyle}>{group.category}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginTop: 4 }}>
                  {group.instruments.map((inst) => (
                    <button
                      key={inst}
                      onClick={() => handleInstrumentChange(inst)}
                      style={{
                        ...quickSelectBtnStyle,
                        background: selectedInstrument === inst ? 'var(--text)' : 'transparent',
                        color: selectedInstrument === inst ? 'var(--bg)' : 'var(--text)',
                        borderColor: selectedInstrument === inst ? 'var(--text)' : 'var(--line)'
                      }}
                    >
                      {instruments.find(i => i.value === inst)?.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
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

const controlLabelStyle: React.CSSProperties = { 
  fontSize: 10, 
  letterSpacing: '0.2em', 
  textTransform: 'uppercase', 
  color: 'var(--muted)', 
  fontFamily: 'var(--font-mono)' 
};

const categoryLabelStyle: React.CSSProperties = {
  fontSize: 9,
  letterSpacing: '0.15em',
  textTransform: 'uppercase',
  color: 'var(--muted)',
  fontFamily: 'var(--font-mono)',
  marginBottom: 2
};

const dropdownStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 36px 10px 14px',
  borderRadius: 6,
  border: '1px solid var(--line)',
  background: 'var(--panel)',
  color: 'var(--text)',
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  appearance: 'none',
  cursor: 'pointer',
  outline: 'none'
};

const dropdownArrowStyle: React.CSSProperties = {
  position: 'absolute',
  right: 12,
  top: '50%',
  transform: 'translateY(-50%)',
  fontSize: 10,
  color: 'var(--muted)',
  pointerEvents: 'none'
};

const quickSelectBtnStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  padding: '6px 10px',
  borderRadius: 4,
  border: '1px solid var(--line)',
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  textAlign: 'left'
};
