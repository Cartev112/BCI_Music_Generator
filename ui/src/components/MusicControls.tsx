import React, { useState } from 'react';
import { Settings } from 'lucide-react';

export function MusicControls() {
  const [preset, setPreset] = useState('consonant');
  const [arpMode, setArpMode] = useState('off');
  const [tempo, setTempo] = useState(100);
  const [beatsChord, setBeatsChord] = useState(2);

  function setPresetSend(v: string) {
    setPreset(v);
    if (window.electronAPI && window.electronAPI.sendOSC) {
      window.electronAPI.sendOSC('music-preset', v);
    }
  }
  function setArpSend(v: string) {
    setArpMode(v);
    if (window.electronAPI && window.electronAPI.sendOSC) {
      window.electronAPI.sendOSC('rhythm-arp_mode', v);
    }
  }
  function setTempoSend(v: number) {
    setTempo(v);
    if (window.electronAPI && window.electronAPI.sendOSC) {
      window.electronAPI.sendOSC('music-tempo', v);
    }
  }
  function setBeatsSend(v: number) {
    setBeatsChord(v);
    if (window.electronAPI && window.electronAPI.sendOSC) {
      window.electronAPI.sendOSC('music-beats_per_chord', v);
    }
  }

  return (
    <div style={panelStyle}>
      <div style={panelHeaderStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Settings width={16} height={16} />
          <span style={panelTitleStyle}>Music Controls</span>
        </div>
        <div style={panelMetaStyle}>generative • adaptive</div>
      </div>
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Preset Selector */}
        <div>
          <div style={controlLabelStyle}>Preset</div>
          <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
            {['consonant', 'jazzy', 'chromatic'].map((p) => (
              <button
                key={p}
                onClick={() => setPresetSend(p)}
                style={{
                  ...controlBtnStyle,
                  background: preset === p ? 'var(--text)' : 'transparent',
                  color: preset === p ? 'var(--bg)' : 'var(--text)',
                  borderColor: preset === p ? 'var(--text)' : 'var(--line)',
                  flex: 1
                }}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Arp Mode */}
        <div>
          <div style={controlLabelStyle}>Arpeggio</div>
          <div style={{ display: 'flex', gap: 4, marginTop: 8, flexWrap: 'wrap' }}>
            {['off', 'up', 'down', 'updown', 'random'].map((m) => (
              <button
                key={m}
                onClick={() => setArpSend(m)}
                style={{
                  ...controlBtnStyle,
                  background: arpMode === m ? 'var(--text)' : 'transparent',
                  color: arpMode === m ? 'var(--bg)' : 'var(--text)',
                  borderColor: arpMode === m ? 'var(--text)' : 'var(--line)',
                  fontSize: 10,
                  padding: '6px 8px',
                  flex: m === 'off' ? '1 0 100%' : '1'
                }}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {/* Tempo Controls */}
        <div>
          <div style={controlLabelStyle}>Tempo: {tempo}</div>
          <div style={{ display: 'flex', gap: 4, marginTop: 8, alignItems: 'center' }}>
            <button 
              onClick={() => setTempoSend(Math.max(60, tempo - 10))}
              style={stepperBtnStyle}
            >
              -10
            </button>
            <button 
              onClick={() => setTempoSend(Math.max(60, tempo - 1))}
              style={stepperBtnStyle}
            >
              -1
            </button>
            <div style={valueDisplayStyle}>{tempo}</div>
            <button 
              onClick={() => setTempoSend(Math.min(200, tempo + 1))}
              style={stepperBtnStyle}
            >
              +1
            </button>
            <button 
              onClick={() => setTempoSend(Math.min(200, tempo + 10))}
              style={stepperBtnStyle}
            >
              +10
            </button>
          </div>
          <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
            {[60, 80, 100, 120, 140, 160].map((bpm) => (
              <button
                key={bpm}
                onClick={() => setTempoSend(bpm)}
                style={{
                  ...presetBtnStyle,
                  background: tempo === bpm ? 'var(--muted)' : 'transparent',
                  color: tempo === bpm ? 'var(--bg)' : 'var(--muted)'
                }}
              >
                {bpm}
              </button>
            ))}
          </div>
        </div>

        {/* Beats per Chord Controls */}
        <div>
          <div style={controlLabelStyle}>Beats/Chord: {beatsChord}</div>
          <div style={{ display: 'flex', gap: 4, marginTop: 8, alignItems: 'center' }}>
            <button 
              onClick={() => setBeatsSend(Math.max(1, beatsChord - 1))}
              style={stepperBtnStyle}
            >
              -
            </button>
            <div style={valueDisplayStyle}>{beatsChord}</div>
            <button 
              onClick={() => setBeatsSend(Math.min(10, beatsChord + 1))}
              style={stepperBtnStyle}
            >
              +
            </button>
          </div>
          <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
            {[1, 2, 4, 8].map((beats) => (
              <button
                key={beats}
                onClick={() => setBeatsSend(beats)}
                style={{
                  ...presetBtnStyle,
                  background: beatsChord === beats ? 'var(--muted)' : 'transparent',
                  color: beatsChord === beats ? 'var(--bg)' : 'var(--muted)',
                  flex: 1
                }}
              >
                {beats}
              </button>
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

const controlBtnStyle: React.CSSProperties = { 
  fontFamily: 'var(--font-mono)', 
  fontSize: 12, 
  letterSpacing: '0.1em', 
  textTransform: 'uppercase', 
  padding: '10px 14px', 
  borderRadius: 6, 
  border: '1px solid var(--line)', 
  cursor: 'pointer',
  transition: 'all 0.15s ease'
};

const stepperBtnStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  padding: '8px 12px',
  borderRadius: 4,
  border: '1px solid var(--line)',
  background: 'transparent',
  color: 'var(--text)',
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  minWidth: 36
};

const valueDisplayStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 16,
  fontWeight: 600,
  color: 'var(--text)',
  minWidth: 44,
  textAlign: 'center',
  padding: '8px 14px',
  border: '1px solid var(--line)',
  borderRadius: 4,
  background: 'var(--panel)'
};

const presetBtnStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  padding: '5px 8px',
  borderRadius: 3,
  border: '1px solid var(--line)',
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  minWidth: 32
};
