# BCI Music Generator – UI Design Specification

## 1. Purpose
Provide a single graphical front-end for operators or performers to:
1. Monitor EEG acquisition quality and classifier outputs.
2. Adjust musical mapping parameters (presets, arpeggio mode, tempo, etc.).
3. Observe and influence the adaptive harmoniser in real time.
4. Start/stop sessions and record logs.

---

## 2. Technology Choice
• **Backend comms:** ZeroMQ or websockets wrapping existing OSC endpoints.  
• **UI Framework:**
  – Electron + React (cross-platform, easy charting) **OR**  
  – PySide6 / Qt (single-binary option, native look).  
Pick based on dev preference – this spec assumes **Electron/React**.

---

## 3. Screen Layout (Desktop 1280×720)
```
┌─────────────────────────────────────────────────────────────┐
│ Top Bar  |  Session timer  ⏵ ⏸ ◼  |  Status LEDs           │
├─────────────────────────────────────────────────────────────┤
│      LEFT PANE                    │        RIGHT PANE       │
│  (EEG & Classifier)               │   (Music Controls)      │
│                                    │                        │
│ • 4-channel EEG waveforms          │ • Preset dropdown      │
│ • Signal quality bars              │ • Adaptive toggle      │
│ • Live PSD plot (alpha, beta…)     │ • Key selector         │
│ • Classifier probability gauge     │ • Tempo slider         │
│ • Detected state indicator         │ • Beats/Chord spinner  │
│                                    │ • Arp mode buttons     │
│                                    │ • Arp rate knob        │
│                                    │ • Density slider       │
│                                    │ • Layer toggles (pad/arp)│
│                                    │                        │
│                                    │ • Console log pane     │
└─────────────────────────────────────────────────────────────┘
```
Responsive: collapsible left pane for small screens; dark-mode palette.

---

## 4. Component Details
### 4.1 EEG Monitor Panel
| Element | Details |
|---------|---------|
| Waveform Plot | 4 stacked scopes, 5-s rolling window (Canvas/WebGL) |
| Quality Bars | Percentage of samples within ±100 µV, color-coded |
| PSD Plot | Alpha, Beta band bars updated every second |
| Marker Log | Table of REST/IMAGERY events |

Data source: subscribe to `brainflow` websocket or parse OSC `/eeg/...` stream.

### 4.2 Classifier Gauge
Circular gauge 0–1 with colored arc (green→red). Tooltip shows numeric probability.

### 4.3 Music Control Panel
• **Preset Dropdown**: values from `presets.py`; on change → OSC `/music/preset`.<br>
• **Adaptive Toggle**: checkbox sends `/music/adaptive 1|0`.<br>
• **Key Selector**: dropdown C ♯ D …; emits `/music/key`.<br>
• **Tempo Slider**: 60–160 BPM; updates `/music/tempo` (controller recalculates beat intervals).<br>
• **Beats-per-Chord Spinner**: 1–8.<br>
• **Arp Mode Buttons**: group (Off, Up, Down, Up-Down, Random). Emits `/rhythm/arp_mode`.
• **Arp Rate Knob**: 0.25–2 beats; `/rhythm/arp_rate`.
• **Density Slider**: 0–1 note-drop probability; `/rhythm/density`.
• **Layer Toggles**: pad / arp / drums checkboxes; map to `/layer/pad 0|1`, etc.

### 4.4 Console Log
Scrollable terminal-style div capturing system messages (same as stdout of Python processes via websocket).

### 4.5 Top Bar
• **Session Timer:** shows elapsed/remaining.  
• **Transport Buttons:** Start = triggers acquisition + classifier + controller scripts; Pause just mutes music; Stop ends session.  
• **Status LEDs:** Board Connect, Classifier OK, OSC link.

---

## 5. Message Mapping
| UI Event | OSC / WebSocket Message |
|----------|------------------------|
| Preset change | `/music/preset <name>` |
| Key change | `/music/key <pc>` |
| Adaptive toggle | `/music/adaptive <0|1>` |
| Tempo | `/music/tempo <bpm>` |
| Arp mode | `/rhythm/arp_mode <mode>` |
| Arp rate | `/rhythm/arp_rate <beats>` |
| Density | `/rhythm/density <0-1>` |
| Transport Start | `/system/start` |
| Transport Stop | `/system/stop` |

Incoming data (to UI):
• `/bci/prob_img` – classifier probability stream.  
• `/music/chord` – latest chord (for display).  
• `/music/note` – arp hits (flash indicator).  
• `/status/*` – connection state.

---

## 6. Implementation Roadmap
1. Bootstrap React-Electron template; set up websocket bridge that listens to OSC and publishes JSON.
2. Build EEG Monitor using `plotly.js` or `react-vis`. Static dummy data first.
3. Implement Music Control panel; wire outbound controls to OSC via backend.
4. Integrate classifier probability gauge.
5. Add session transport & logging.
6. Package cross-platform installers (Electron Builder).

---

## 7. Stretch Features
• Mobile companion view (WebRTC) for remote monitoring.  
• Theme editor (custom color palettes).  
• Recording management (start/stop saving EEG and OSC logs).  
• Wizard for electrode placement checklist.

---
*Draft v0.1 – subject to iterative UX testing.* 