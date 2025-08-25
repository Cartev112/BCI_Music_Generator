import React, { useEffect, useMemo, useRef, useState } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
// removed live config editor
import { Activity, Brain, CircuitBoard, Gauge, LineChart, ServerCog, Settings, Signal, Sun, Moon, PlugZap, Play, Pause, Save, LogOut } from 'lucide-react';
import { MusicControls } from '../components/MusicControls';
import { EEGSimulator } from '../components/EEGSimulator';
import { InstrumentDropdown } from '../components/InstrumentDropdown';
import { BCIStatus } from '../components/BCIStatus';
import { MIDIVisualizer } from '../components/MIDIVisualizer';

export default function ControlRoom() {
  const [dark, setDark] = useState(true);
  const chartRef = useRef<HTMLDivElement | null>(null);
  const uplotRef = useRef<uPlot | null>(null);
  const [connected, setConnected] = useState(false);
  const [statusFlags, setStatusFlags] = useState({ board: false, classifier: false, osc: false });
  const [simEnabled, setSimEnabled] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const sampleCounterRef = useRef(0);



  // EEG buffers (4 channels)
  const buffersRef = useRef<number[][]>([[], [], [], []]);
  const MAX_POINTS = 2000; // hard cap
  const VISIBLE_POINTS = 50; // render only a short window

  // Hook to incoming samples from Electron
  useEffect(() => {
    // Only set up electronAPI listeners if running in Electron context
    if (window.electronAPI && window.electronAPI.onSample && window.electronAPI.onStatus) {
      window.electronAPI.onSample((arr) => {
        if (simEnabled) return; // ignore real samples while simulating
        const b = buffersRef.current;
        for (let i = 0; i < 4; i++) {
          const v = Number(arr[i] ?? 0);
          b[i].push(v);
          if (b[i].length > MAX_POINTS) b[i].shift();
        }
        sampleCounterRef.current += 1;
      });
      window.electronAPI.onStatus('board', (v) => setStatusFlags((s) => ({ ...s, board: !!v })));
      window.electronAPI.onStatus('classifier', (v) => setStatusFlags((s) => ({ ...s, classifier: !!v })));
      window.electronAPI.onStatus('osc', (v) => setStatusFlags((s) => ({ ...s, osc: !!v })));
    }
  }, [simEnabled]);



  useEffect(() => {
    setConnected(statusFlags.board && statusFlags.classifier && statusFlags.osc);
  }, [statusFlags]);

  // Session control functions
  const handlePlayPause = () => {
    if (window.electronAPI && window.electronAPI.sendSystem) {
      if (isPlaying) {
        window.electronAPI.sendSystem('pause');
      } else {
        window.electronAPI.sendSystem('start');
      }
    }
    setIsPlaying(!isPlaying);
  };

  const handleSave = () => {
    if (window.electronAPI && window.electronAPI.sendSystem) {
      window.electronAPI.sendSystem('stop');
    }
    setIsPlaying(false);
    // Could add save notification here
  };

  const handleLeave = () => {
    // Navigate back to home or previous page
    window.location.hash = '#/home';
  };



  // uPlot chart, updated efficiently
  useEffect(() => {
    if (!chartRef.current) return;

    const plotWidth = chartRef.current.clientWidth || 800;
    const plotHeight = 360;

    const opts: uPlot.Options = {
      width: plotWidth,
      height: plotHeight,
      scales: { x: { time: false }, y: { auto: true } },
      axes: [
        { 
          stroke: '#9a9a9a', 
          grid: { stroke: '#121212' }, 
          values: (u, vals) => vals.map(v => v.toFixed(0)),
          label: 'Sample',
          labelSize: 12,
          labelFont: 'var(--font-mono)',
          size: 40
        },
        { 
          stroke: '#9a9a9a', 
          grid: { stroke: '#121212' }, 
          values: (u, vals) => vals.map(v => v.toFixed(1) + ' µV'),
          label: 'Amplitude (µV)',
          labelSize: 12,
          labelFont: 'var(--font-mono)',
          size: 60
        },
      ],
      legend: { show: false },
      cursor: { show: false },
      series: [
        {},
        { label: 'Ch1', stroke: '#ffffff', width: 2 }, // white
        { label: 'Ch2', stroke: '#34d399', width: 2 },  // green
        { label: 'Ch3', stroke: '#60a5fa', width: 2 },  // blue
        { label: 'Ch4', stroke: '#ef4444', width: 2 },  // red
      ],
    };

    const u = new uPlot(opts, [new Float64Array(0), new Float64Array(0), new Float64Array(0), new Float64Array(0), new Float64Array(0)], chartRef.current);
    uplotRef.current = u;

    const MAX_PLOT_POINTS = 600; // decimated for performance
    const update = () => {
      const b = buffersRef.current;
      const n = Math.min(b[0].length, VISIBLE_POINTS);
      const step = Math.max(1, Math.floor(n / MAX_PLOT_POINTS));
      const len = Math.floor(n / step);
      const x = new Float64Array(len);
      const c1 = new Float64Array(len);
      const c2 = new Float64Array(len);
      const c3 = new Float64Array(len);
      const c4 = new Float64Array(len);
      let idx = 0;
      const start = Math.max(0, b[0].length - n);
      const xStart = Math.max(0, sampleCounterRef.current - n);
      for (let i = 0; i < n; i += step) {
        x[idx] = xStart + i;
        c1[idx] = b[0][start + i] || 0;
        c2[idx] = b[1][start + i] || 0;
        c3[idx] = b[2][start + i] || 0;
        c4[idx] = b[3][start + i] || 0;
        idx++;
      }
      u.setData([x, c1, c2, c3, c4]);
    };

    const id = setInterval(update, 80); // ~12.5 fps
    const onResize = () => {
      if (!chartRef.current) return;
      u.setSize({ width: chartRef.current.clientWidth || 800, height: plotHeight });
    };
    window.addEventListener('resize', onResize);
    update();

    return () => {
      clearInterval(id);
      window.removeEventListener('resize', onResize);
      u.destroy();
      uplotRef.current = null;
    };
  }, [dark]);

  // console removed for now

  const sessionId = useMemo(() => Math.random().toString(16).slice(2, 10).toUpperCase(), []);

  return (
    <div className={dark ? 'dark' : 'light'}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');
        :root {
          --bg: #000000;
          --panel: #0a0a0a;
          --muted: #9a9a9a;
          --text: #ffffff;
          --line: #1a1a1a;
          --grid: #101010;
          --font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
        }
        .light {
          --bg: #ffffff;
          --panel: #f5f5f5;
          --muted: #333333;
          --text: #000000;
          --line: #e5e5e5;
          --grid: #efefef;
        }
        html, body, #root { height: 100%; }
      `}</style>

      <div className="min-h-screen" style={{ background: 'var(--bg)', color: 'var(--text)', display: 'flex', fontFamily: 'var(--font-mono)', minHeight: '100vh' }}>
        {/* Sidebar */}
        <aside style={{ display: 'none' }} />

        {/* Main column */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {/* Top bar */}
          <header style={{ height: 56, borderBottom: '1px solid var(--line)', background: 'color-mix(in oklab, var(--panel) 90%, transparent)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Gauge width={16} height={16} />
              <h1 style={{ fontSize: 14, letterSpacing: '0.18em', textTransform: 'uppercase' }}>Mastermind Console</h1>
              <span style={{ 
                color: connected ? '#10b981' : 'var(--muted)', 
                fontSize: 12, 
                letterSpacing: '0.2em', 
                textTransform: 'uppercase',
                textShadow: connected ? '0 0 8px #10b981' : 'none'
              }}>
                <span style={{ 
                  color: connected ? '#10b981' : 'var(--muted)',
                  textShadow: connected ? '0 0 8px #10b981' : 'none'
                }}>•</span> {connected ? 'live' : 'idle'}
              </span>
            </div>
            
            {/* Centered Icons */}
            <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* Session Controls */}
              <button 
                onClick={handlePlayPause} 
                style={{ 
                  ...btnStyle, 
                  color: 'var(--text)', 
                  background: isPlaying ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                  borderColor: isPlaying ? '#10b981' : 'var(--line)'
                }}
                aria-label={isPlaying ? 'Pause session' : 'Start session'}
              >
                {isPlaying ? <Pause width={14} height={14} /> : <Play width={14} height={14} />}
              </button>
              <button onClick={handleSave} style={{ ...btnStyle, color: 'var(--text)' }} aria-label="Save session">
                <Save width={14} height={14} />
              </button>
              <button onClick={handleLeave} style={{ ...btnStyle, color: 'var(--text)' }} aria-label="Leave session">
                <LogOut width={14} height={14} />
              </button>
              
              {/* Divider */}
              <div style={{ width: 1, height: 20, background: 'var(--line)', margin: '0 4px' }} />
              
              {/* System Controls */}
              <button 
                onClick={() => setConnected((c) => !c)} 
                style={{ 
                  ...btnStyle, 
                  color: 'var(--text)',
                  background: connected ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                  borderColor: connected ? '#10b981' : 'var(--line)'
                }}
              >
                <PlugZap width={14} height={14} />
              </button>
              <button onClick={() => setDark((d) => !d)} style={{ ...btnStyle, color: 'var(--text)' }} aria-label="Toggle theme">
                {dark ? <Sun width={14} height={14} /> : <Moon width={14} height={14} />}
              </button>
              <button onClick={() => setSimEnabled((v) => !v)} style={{ ...btnStyle, borderColor: simEnabled ? '#ffffff' : 'var(--line)', color: 'var(--text)' }} aria-label="Toggle EEG simulator">
                <Activity width={14} height={14} />
              </button>
            </div>
            
            {/* Right spacer to balance layout */}
            <div style={{ width: 0 }}></div>
          </header>

          {/* Status LEDs + KPIs - Left Half Only */}
          <section style={{ display: 'flex', justifyContent: 'flex-start', padding: '16px 16px 0 16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(0,1fr))', gap: 12, width: '50%' }}>
              {[{label:'BOARD', on: statusFlags.board}, {label:'CLASSIFIER', on: statusFlags.classifier}, {label:'OSC', on: statusFlags.osc}, {label:'EEG', on: buffersRef.current[0].length>0}, {label:'SIM', on: simEnabled}].map((it) => (
                <div key={it.label} style={{ ...cardStyle, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                  <div style={kpiLabelStyle}>{it.label}</div>
                  <span style={{ width:12, height:12, borderRadius:12, background: it.on ? '#10b981' : '#374151', boxShadow: it.on ? '0 0 12px #10b981' : 'none' }} />
                </div>
              ))}
            </div>
          </section>

           {/* Main grid */}
           <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 16, padding: 16, paddingBottom: 24, flex: 1 }}>
            {/* Left Column - Charts */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* EEG Chart panel */}
              <div style={panelStyle}>
                <div style={panelHeaderStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <LineChart width={16} height={16} />
                    <span style={panelTitleStyle}>Neural Channels</span>
                  </div>
                  <div style={panelMetaStyle}>µV • streaming</div>
                </div>
                <div style={{ padding: '0 16px 6px', color: 'var(--muted)', fontSize: 10, letterSpacing: '0.24em', textTransform: 'uppercase', display: 'flex', gap: 16 }}>
                  <LegendSwatch color="#ffffff" label="Ch1" />
                  <LegendSwatch color="#34d399" label="Ch2" />
                  <LegendSwatch color="#60a5fa" label="Ch3" />
                  <LegendSwatch color="#ef4444" label="Ch4" />
                </div>
                <div ref={chartRef} style={{ height: 280, width: '100%' }} />
              </div>

              {/* MIDI Visualizer */}
              <MIDIVisualizer width={800} height={180} />
            </div>

            {/* Control Panels Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* BCI Status Panel */}
              <BCIStatus />
              
              {/* Music Controls Panel */}
              <MusicControls />
            </div>

            {/* Instrument Selection Panel */}
            <InstrumentDropdown />
          </div>
          
          {/* EEG Simulator Component (no UI, just logic) */}
          <EEGSimulator 
            enabled={simEnabled}
            buffersRef={buffersRef}
            sampleCounterRef={sampleCounterRef}
            maxPoints={MAX_POINTS}
          />
        </div>
      </div>
    </div>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span
        style={{
          display: 'inline-block',
          width: 32,
          height: 2,
          background: color,
        }}
      />
      <span style={{ fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)' }}>{label}</span>
    </div>
  );
}

const cardStyle: React.CSSProperties = { borderRadius: 12, border: '1px solid var(--line)', background: 'color-mix(in oklab, var(--panel) 90%, transparent)', padding: 16, boxShadow: '0 1px 2px rgba(0,0,0,0.2)' };
const panelStyle: React.CSSProperties = { borderRadius: 12, border: '1px solid var(--line)', background: 'color-mix(in oklab, var(--panel) 90%, transparent)', overflow: 'hidden' };
const panelHeaderStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--line)' };
const panelTitleStyle: React.CSSProperties = { fontSize: 12, letterSpacing: '0.16em', textTransform: 'uppercase' };
const panelMetaStyle: React.CSSProperties = { fontSize: 10, color: 'var(--muted)', letterSpacing: '0.2em', textTransform: 'uppercase' };
const kpiLabelStyle: React.CSSProperties = { fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)' };
const btnStyle: React.CSSProperties = { display: 'inline-flex', alignItems: 'center', gap: 8, borderRadius: 8, border: '1px solid var(--line)', padding: '6px 12px', fontSize: 12, background: 'transparent' };




