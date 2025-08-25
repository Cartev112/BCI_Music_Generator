# BCI Music Generation System - Planning Document

## 1. Project Goal

To develop a Brain-Computer Interface (BCI) system that:
1.  Acquires EEG signals using a Ganglion board (4 channels).
2.  Processes these signals in near real-time.
3.  Classifies user mental states, specifically focusing on detecting periods of active mental imagery versus baseline/rest states.
4.  Uses the classified states to modulate simple parameters of a generative music algorithm (to be implemented in a later phase).

## 2. Hardware

*   **EEG Device:** OpenBCI Ganglion Board
*   **Electrodes:** 4 channels.
*   **Proposed Placement (Refined Recommendation):**
    *   **Primary:** O1, O2 (Occipital Lobe): Critical for capturing visual imagery correlates (Alpha band modulation).
    *   **Secondary Option 1 (Recommended):** P3, P4 (Parietal Lobe): Involved in spatial/attentional networks, generally less EOG artifact contamination than frontal sites.
    *   **Secondary Option 2:** Fp1, Fp2 (Frontal Lobe): May capture 'effort' but highly susceptible to eye artifacts. Requires careful artifact management.
    *   **Reference/Ground:** Mastoids (A1/A2) or earlobes.

## 3. Software Stack (Potential)

*   **Language:** Python
*   **Core Libraries:**
    *   `BrainFlow`: For interfacing with the Ganglion board and acquiring data.
    *   `NumPy`: For numerical operations.
    *   `SciPy`: For scientific computing, including signal processing functions (filtering).
    *   `MNE-Python`: Comprehensive EEG analysis toolkit (filtering, artifact handling, epoching, feature extraction, visualization).
    *   `Scikit-learn`: For machine learning (SVM, cross-validation, performance metrics).
*   **Real-time:**
    *   Python's built-in `threading` or `multiprocessing`.
    *   Possibly LabStreamingLayer (LSL) if using separate acquisition/processing components.
*   **Music Generation (Later):** `python-osc` (for sending control signals), a DAW (like Ableton Live, Reaper) or a dedicated music environment (Max/MSP, Pure Data, SuperCollider), or a Python music library (`Mingus`, `Music21` - though potentially less suitable for real-time generative audio).

## 4. Data Acquisition Strategy

*   **Task Paradigm:** Cued Mental Imagery vs. Rest.
    *   **Imagery Task:** Ask the user to perform a specific, consistent mental imagery task (e.g., vividly visualizing a rotating cube, imagining a specific familiar face, recalling a detailed memory). Consistency is key.
    *   **Rest Task:** Ask the user to relax, keep eyes open or closed (be consistent), and avoid specific mental tasks (e.g., count backwards from 10 slowly).
    *   **Trial Structure:** Block design (e.g., 10s Rest, 10s Imagery, repeated N times) with clear visual or auditory cues.
*   **Data Recording:**
    *   Use BrainFlow or OpenBCI GUI (with LSL) to stream and record data.
    *   Save data in a standard format (e.g., BrainFlow's default, CSV, or convert to FIF using MNE).
    *   Crucial: Record event markers/timestamps precisely indicating the start/end of each task condition (Rest/Imagery).
*   **Initial Goal:** Collect a robust dataset from a single user for initial model development and feasibility testing. Aim for **at least 30-50 clean trials per class (Rest and Imagery)**. Assuming ~10s per trial, this equates to roughly 10-15 minutes of core task data, suggesting a ~20-30 minute recording session.

## 5. Signal Processing Pipeline (Offline First)

1.  **Loading Data:** Load recorded sessions.
2.  **Filtering:**
    *   **Band-pass:** ~1 Hz to 40 Hz (or higher, e.g., 50Hz) to remove DC drift and high-frequency noise.
    *   **Notch:** 50 Hz or 60 Hz (depending on local power line frequency) to remove electrical interference.
3.  **Referencing:** Re-reference data if necessary (e.g., to average reference or linked mastoids if recorded).
4.  **Artifact Handling (Challenging with 4 channels):**
    *   **Visual Inspection:** Identify and potentially reject segments with gross muscle artifacts (EMG) or signal loss.
    *   **Filtering:** Aggressive low-pass filtering might reduce EMG, but also valuable gamma activity.
    *   **EOG:** Frontal channels (Fp1, Fp2) will be heavily contaminated by eye blinks/movements. Independent Component Analysis (ICA) is standard but often requires more channels. Simpler methods like regression based on EOG channels (if available) or simply rejecting trials with large EOG artifacts might be necessary.
    *   *Initial Strategy:* Focus on clean data collection protocols, visual rejection, and robust filtering.
5.  **Epoching:** Segment the continuous data into epochs (time windows) corresponding to the task conditions (e.g., 2-8 seconds within each Imagery/Rest block, avoiding transition periods).
6.  **Feature Extraction:** Calculate features for each epoch that might differentiate the states.
    *   **Power Spectral Density (PSD):** Calculate power in different frequency bands (e.g., Delta (1-4Hz), Theta (4-8Hz), Alpha (8-13Hz), Beta (13-30Hz), Low Gamma (30-50Hz)) for each channel. Occipital alpha power (decrease during visual imagery) is a classic target.
    *   **Band Power Ratios:** e.g., Alpha/Beta ratio.
    *   **Time-domain features:** Mean, variance, Hjorth parameters (Activity, Mobility, Complexity).
    *   *Note:* Common Spatial Patterns (CSP) is effective for motor imagery but requires more channels and distinct spatial patterns, likely less suitable here.

## 6. Machine Learning (Offline First)

1.  **Feature Matrix:** Create a matrix where rows are epochs and columns are the extracted features.
2.  **Labels:** Assign a label (e.g., 0 for Rest, 1 for Imagery) to each epoch.
3.  **Model Selection:**
    *   **Primary Candidates:**
        *   **Linear Discriminant Analysis (LDA):** Fast, simple, often effective BCI baseline. Good starting point.
        *   **Support Vector Machine (SVM):** Test both Linear and RBF kernels. RBF can capture non-linearities. Good performance common in BCI.
    *   **Others (Later):** Logistic Regression, Simple Neural Networks (MLP).
4.  **Training & Validation:**
    *   **Split:** Divide data into training and testing sets (e.g., 80%/20%). Ensure chronological split or use cross-validation that respects trial structure (e.g., Leave-One-Session-Out or K-Fold on trials).
    *   **Cross-Validation:** Use K-Fold cross-validation on the training set to tune hyperparameters (e.g., SVM's C and gamma parameters).
    *   **Scaling:** Standardize features (e.g., zero mean, unit variance) before training.
5.  **Evaluation Metrics:**
    *   **Accuracy:** Overall correctness (use with caution if classes are imbalanced).
    *   **Precision, Recall, F1-Score:** Better for understanding performance per class.
    *   **ROC AUC:** Evaluates discriminability across different thresholds.
    *   **Confusion Matrix:** Visualize correct/incorrect classifications per class.

## 7. Real-Time System Outline

1.  **Data Acquisition:** Continuously acquire small chunks of data via BrainFlow.
2.  **Buffering:** Store incoming data in a rolling buffer.
3.  **Processing:** Apply the *same* signal processing steps (filtering, etc.) as offline, adapted for real-time chunks.
4.  **Feature Extraction:** Calculate features on the latest processed window.
5.  **Classification:** Feed extracted features into the *pre-trained* model to get a prediction (Imagery/Rest).
6.  **Decision Smoothing:** Apply a smoothing logic (e.g., require N consecutive predictions of the same class, or use a moving average of probabilities) to avoid overly rapid switching.
7.  **Output:** Trigger music parameter changes based on the smoothed classification output (e.g., send OSC messages).

## 8. Challenges & Mitigation Strategies

*   **Low SNR:** Maximize signal quality via proper skin prep, electrode contact, minimizing external noise.
*   **Artifacts:** Strict instructions to user (minimize blinking/movement during trials), visual inspection/rejection, potentially adaptive filtering (use with care).
*   **Low Spatial Resolution:** Focus on features known to be less spatially specific or prominent at chosen locations (e.g., Occipital Alpha, Frontal Theta/Beta). Feature engineering becomes critical.
*   **Imagery Consistency/Detection:** The biggest challenge. Start with *very distinct* states (intense imagery vs. deep relaxation). User training and feedback are essential. Ensure the chosen imagery task reliably modulates EEG (e.g., visual imagery affecting Occipital Alpha).
*   **Variability (Inter/Intra-subject):** Models trained on one user/session may not generalize well. Requires calibration/re-training. Adaptive algorithms could be explored later.
*   **Real-time Constraints:** Optimize processing pipeline. Feature selection to use only the most informative *and* computationally cheap features. Test processing time per window.

## 9. Brainstorming: Enhancing Accuracy, Feasibility, Functionality

*   **Accuracy:**
    *   **Better Features:** Explore phase-based features, connectivity measures (coherence, phase-locking value between channels - might be noisy), non-linear features.
    *   **Feature Selection:** Use techniques (e.g., Recursive Feature Elimination, Mutual Information) to select the most discriminative subset of features, especially if initial performance is low.
    *   **Advanced Artifact Rejection:** If possible, explore algorithms robust to few channels, or focus heavily on data cleaning.
    *   **Ensemble Methods:** Combine predictions from multiple models (e.g., SVM + LDA).
    *   **Refined Task Design:** Experiment with different types of mental imagery known to have clearer EEG correlates.
*   **Feasibility:**
    *   **Simplify Initial Goal:** Classify 'Cognitive Load/Effort' vs. 'Rest' instead of specific imagery first. This might be more robust.
    *   **User Training:** Provide feedback to the user during training sessions to help them learn to produce more distinct brain states.
    *   **Robust Baseline:** Ensure the 'Rest' state is well-defined and consistently achievable.
    *   **Offline First:** Thoroughly validate the pipeline offline before attempting real-time. Start with LDA and SVM.
*   **Functionality:**
    *   **Calibration Phase:** Include a short calibration session before each use to adapt the classifier.
    *   **Confidence Threshold:** Only trigger music changes when the classifier's confidence is high.
    *   **Continuous Control:** Instead of binary classification, map a feature (e.g., Alpha power) or classifier probability directly to a music parameter for smoother modulation.
    *   **Feedback:** Provide clear feedback to the user about their detected state (visual or simple auditory cue) to help them control the system.
    *   **Adaptive Learning:** (Advanced) Allow the system to slowly adapt over time based on ongoing performance or user feedback.

## 10. Development Phases

1.  **Phase 1: Setup & Data Collection:** Hardware setup, software install, implement data acquisition script with event markers, collect initial labeled dataset (Imagery vs. Rest).
2.  **Phase 2: Offline Analysis & Modeling:** Implement signal processing pipeline, feature extraction, train and evaluate initial classifiers (SVM, LDA). Assess feasibility based on offline accuracy.
3.  **Phase 3: Real-time Prototype (Classification Only):** Implement real-time data acquisition and processing loop, apply pre-trained model, output classifications (e.g., print to console).
4.  **Phase 4: Basic Music Integration:** Choose a simple music modulation strategy (e.g., OSC messages controlling volume/filter cutoff in a DAW/synth), link real-time classifier output to music control.
5.  **Phase 5: Refinement & Testing:** Improve pipeline, retrain models, enhance music mapping, conduct user testing and gather feedback.

---
*This document provides a starting point and will evolve as the project progresses.*


### BCI Music System – Architecture and Operation (Current State)

## 1. Purpose and Scope
This document explains the current BCI music system end-to-end: what it does, how it’s structured, how data flows between components, the runtime lifecycle, session data handling, configuration, and how to run and develop it. It reflects the system as it exists now.

## 2. High-level Overview
- EEG data is acquired from a Ganglion board (BrainFlow).
- A real-time classifier processes sliding windows, extracts features, loads a trained joblib model, and outputs predictions/probabilities.
- The classifier publishes OSC messages with status and imagery probability; the UI and music controller subscribe.
- The music controller schedules chords and arpeggios and maps the classifier state/probability into musical changes. It logs musical events into SQLite.
- An Electron UI serves as the operator console: device setup, session monitoring (EEG quality, PSD, probability), and musical controls. It relays control changes to the music controller via OSC, and provides session history.

## 3. Core Components

### 3.1 Data Acquisition (recorded datasets)
- Location: `datatraintest/data_acquisition.py`
- Functionality:
  - Connects to Ganglion via BrainFlow. Records raw data for a set duration.
  - Allows manual marker insertion for REST/IMAGERY via keyboard.
  - Saves raw (CSV) via BrainFlow’s `DataFilter.write_file`.
- Intended use:
  - Offline training datasets preparation; not used in the live performance loop.
- Current notes:
  - CLI options: serial port, duration, output filename, logging, etc.
  - Example use:
    - python datatraintest/data_acquisition.py --serial-port COM3 --duration 120 --output-file my_session

### 3.2 Real-time Classifier
- Location: `real_time_classifier.py`
- Purpose: Acquire EEG windows in real-time, extract features, run a trained model, publish results via OSC.
- Key behaviors:
  - BrainFlow streaming into a rolling buffer.
  - Sliding window processing with overlap (configurable window size and step).
  - Filtering: bandpass/lowpass/highpass/notch, and common average referencing.
  - Feature extraction via `features.py` (delegation to `datatraintest/features.py` when available).
  - Classification with a joblib-loaded model; optional probability outputs.
  - OSC outputs:
    - `/status/board 1`, `/status/classifier 1`, `/status/osc 1` (status heartbeats for UI).
    - `/bci/prob_img <float>` (probability of imagery) when enabled.
    - `/bci/state <0|1>` (REST/IMAGERY) when confirmed by smoothing logic.
- Sliding window correctness:
  - Buffer built sample-by-sample; converted to shape (n_channels, window_samples) for feature computation (fixed).
- CLI example:
  - python real_time_classifier.py --serial-port COM3 --model-path model.joblib --enable-osc --send-prob --osc-ip 127.0.0.1 --osc-port 9000

```137:161:real_time_classifier.py
def main():
    args = parse_args()
    rtbci = RealTimeBCI(args)
    rtbci.start()
```

### 3.3 Feature Extraction
- Location: `datatraintest/features.py` (authoritative) and shim `features.py`.
- The shim:
  - Tries to import from `datatraintest/features.py`.
  - Falls back to a minimal implementation if the training module is not present, to avoid runtime import errors.
- Primary features:
  - Bandpowers (delta/theta/alpha/beta/gamma), relative bandpowers, alpha/beta ratio, Hjorth parameters per channel; concatenated across channels.

### 3.4 Music Controller
- Location: `music_controller.py`
- Inputs:
  - OSC: `/bci/prob_img`, `/bci/state` from classifier.
  - OSC controls from UI: `/music/preset`, `/music/tempo`, `/music/beats_per_chord`, `/music/adaptive`, `/music/key`, `/rhythm/arp_mode`, `/rhythm/arp_rate`, `/rhythm/density`, plus layer toggles.
- Outputs:
  - `/music/chord` (root, quality, prob, and pitches),
  - `/music/note` (arp notes).
- Operation:
  - Scheduler loop computes beat/chord intervals from BPM and beats-per-chord.
  - Uses `TensionHarmonizer` or `AdaptiveTensionHarmonizer` to select next chords.
  - Uses `Arpeggiator` to emit arp pitches at sub-beat intervals.
- Session logging (see below) records chords and notes.
- Runtime parameter updates:
  - UI OSC handlers update live parameters (BPM, key, adaptive, arp…).
- Graceful lifecycle:
  - Ensures scheduler timing is initialized; ends session logging on shutdown.

### 3.5 Session Logging and Persistence
- Location: `session_logger.py`
- Storage: SQLite database at `data/sessions.db`. On startup, schema is ensured/migrated.
- Tables:
  - `sessions`: start/end timestamps and configuration (preset, key, bpm, beats_per_chord, adaptive, arp_mode, arp_rate, density).
  - `chords`: chord events (root, quality, pitches).
  - `notes`: arpeggiated notes (pitch, velocity).
  - `probs`: classifier probability timeline (optional hook via `log_prob()`; controller could also log if desired).
- API:
  - `start_session(...)` returns session_id.
  - `log_chord`, `log_note`, `log_prob`.
  - `end_session()` finalizes the session.
  - `list_sessions(limit)` lists recent sessions (used by UI).

```37:75:session_logger.py
class SessionLogger:
    def __init__(...):
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        self.session_id = None
        self._ensure_columns()
...
    def start_session(self, preset: str, key: str, bpm: int, beats_per_chord: int,
                      adaptive: int = 0, arp_mode: str = 'off', arp_rate: float = 1.0, density: float = 0.5):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO sessions (start_ts, preset, key, bpm, beats_per_chord, adaptive, arp_mode, arp_rate, density)
             VALUES (?,?,?,?,?,?,?,?,?)",
            (time.time(), preset, key, bpm, beats_per_chord, int(adaptive), arp_mode, float(arp_rate), float(density)),
        )
```

## 4. UI (Electron + React + TypeScript)
- Location: `ui/`
- Framework:
  - Electron main process bridges OSC and the renderer via IPC.
  - Renderer built with Vite + React + TypeScript; MUI for modern components; HashRouter for routing under file://.
  - Security: context isolation, no node integration; API exposed via `preload.js`.
- Key pages:
  - Home: Big title “Brain Jazz”, buttons: New Session, Session History, Settings.
  - Setup: Connection status (Board/Classifer/OSC), “Live Check” of probability, Quick Tips, Continue and Dev Bypass.
  - Session: Top bar with transport and LEDs; left pane for probability, EEG signal quality, EEG waveforms, PSD; right pane: music controls and additional controls; console log.
  - History: Renders recent sessions from the app’s session store (Electron local persists) and controller DB summaries.
- Visuals:
  - Dark theme, Roboto typography, vivid colors, rounded cards.
  - EEG waveforms via uPlot; PSD calculated in a Web Worker; signal quality as progress bars.

```39:76:ui/src/pages/Setup.tsx
React.useEffect(() => {
  window.electronAPI.onStatus('board', (v) => setStatus((s) => ({ ...s, board: v })));
  window.electronAPI.onStatus('classifier', (v) => setStatus((s) => ({ ...s, classifier: v })));
  window.electronAPI.onStatus('osc', (v) => setStatus((s) => ({ ...s, osc: v })));
  window.electronAPI.on('bci-prob', (v) => setProb(Number(v) || 0));
}, []);
```

### 4.1 Electron main process
- Location: `ui/main.js`
- Responsibilities:
  - Opens UDP OSC in/out.
  - Forwards selected incoming OSC messages to renderer channels (probability, EEG, markers, status).
  - Handles renderer IPC commands for outbound OSC (controls, transport).
  - Provides a lightweight session list endpoint; also persists simple session summaries under Electron userData.
- Status mapping from OSC to renderer:

```19:36:ui/main.js
udpIn.on('message', (msg) => {
  ...
  else if (msg.address.startsWith('/status/')) {
    const key=msg.address.split('/')[2];
    if(['board','classifier','osc'].includes(key))
      mainWin.webContents.send('status-'+key, !!msg.args[0]);
  }
  mainWin.webContents.send('console-log', { t: Date.now(), address: msg.address, args: msg.args || [] });
});
```

## 5. Message Map (OSC and IPC)

- From classifier:
  - `/status/board <1|0>`
  - `/status/classifier <1|0>`
  - `/status/osc <1|0>`
  - `/bci/prob_img <float 0..1>`
  - `/bci/state <0|1>` (only when smoothing confirms state)
- From UI to music controller:
  - `/music/preset <name>`
  - `/music/tempo <bpm>`
  - `/music/beats_per_chord <int>`
  - `/music/adaptive <0|1>`
  - `/music/key <string>`
  - `/rhythm/arp_mode <mode>`
  - `/rhythm/arp_rate <float beats>`
  - `/rhythm/density <0..1>`
  - `/layer/pad|arp|drums <0|1>`
  - `/system/start|pause|stop` (transport; can be used to coordinate multiple processes)
- From music controller to UI:
  - `/music/chord <root> <quality> <prob> <pitches...>`
  - `/music/note <pitch> <velocity>`
- Electron IPC from renderer:
  - `music-preset`, `music-tempo`, etc. mapped one-to-one to OSC
  - `system-start`, `system-stop`, `system-pause`
  - `list-sessions` (returns cached Electron-side sessions for UI History view)

## 6. Runtime Lifecycle

### 6.1 Setup
- Start classifier with OSC enabled. It emits status heartbeats immediately so the Setup LEDs turn green.
- Start music controller. It listens for `/bci/prob_img` and accepts UI control messages.

### 6.2 Session start
- In the UI session page, press Play. That sends `/system/start`. Electron records a simple session entry locally (used by the UI), and the controller starts/continues emitting chords/arp and logging in SQLite.

### 6.3 Ongoing operation
- Classifier publishes `/bci/prob_img` continuously. UI probability gauge and plot update.
- UI controls (preset, key, tempo, adaptive, arp, density, layers) send OSC to the controller. Controller updates internal parameters.

### 6.4 Session stop
- In the UI, press Stop. Electron’s local session ends, music controller cleans up and finalizes the SQLite session. UI History shows recent sessions.

## 7. Session Data – What’s Saved

### 7.1 Electron (UI-side)
- Minimal session summaries (id, start/end, settings) are stored in app userData for fast UI listing. This is mainly a convenience for the UI.

### 7.2 Controller (authoritative, SQLite)
- `sessions`: start/end, preset, key, bpm, beats_per_chord, adaptive, arp_mode, arp_rate, density.
- `chords`: root, quality, and emitted pitches with timestamps.
- `notes`: arp pitches and velocities with timestamps.
- `probs`: optional probability time series (hook available via `log_prob`; can be called by classifier or controller if desired).

## 8. Configuration and CLI

### 8.1 Classifier
- Key args:
  - `--serial-port`, `--model-path`
  - `--window-size`, `--step-size`, `--smooth-n`
  - `--enable-osc`, `--send-prob`, `--osc-ip`, `--osc-port`
- Example:
  - python real_time_classifier.py --serial-port COM3 --model-path model.joblib --enable-osc --send-prob --osc-ip 127.0.0.1 --osc-port 9000

### 8.2 Controller
- Key args:
  - `--listen-port` (default 9000), `--out-ip`, `--out-port`
  - `--bpm`, `--beats-per-chord`, `--key`, `--adaptive`
  - `--preset`, `--arp-mode`, `--arp-rate`, `--arp-vel`
- Example:
  - python music_controller.py --listen-port 9000 --out-ip 127.0.0.1 --out-port 9001 --bpm 100 --beats-per-chord 2 --key C --arp-mode up --arp-rate 0.5

### 8.3 UI commands
- In `ui/`:
  - Development: `npm run dev` (starts Vite + Electron; hot reload)
  - Production: `npm run build` then `npm start`

## 9. Performance and Reliability
- Classifier windowing fixed to avoid unnecessary transposes; uses a deque buffer.
- EEG plotting uses uPlot with typed arrays and requestAnimationFrame batching.
- PSD computed in a Web Worker to avoid UI thread stalls.
- Electron UI uses context isolation and no Node in renderer.
- Controller uses a dedicated thread for scheduling chords/arp and tries to maintain timing.
- Status heartbeats ensure UI LEDs provide immediate connection state feedback.

## 10. Developer Experience
- UI:
  - React + TypeScript + Vite; MUI for components; HashRouter.
  - Clean separation of Electron main (bridging OSC/IPC) and renderer.
- Python:
  - Clear CLIs, modular feature extraction, and logging to SQLite via `SessionLogger`.
- Local testing:
  - Dev Bypass on Setup page to preview the session UI without hardware.
  - Console log panel to view incoming OSC in the UI.

## 11. Known Gaps and Next Upgrades
- Centralized configuration and logging modules for Python services (YAML/env, rotating logs).
- WebSocket bridge service to complement/replace OSC for UI transport (simplifies cross-machine UI).
- Fill in controller layer toggles and more detailed state mapping (e.g., density-driven note thinning).
- Optionally log probability time series into SQLite via a small companion in the classifier.
- Export tools in UI History (CSV/JSON), and filters to inspect sessions.
- Multi-user profiles and calibration workflows.

## 12. Quick Start Checklist
- Train a model offline and export `model.joblib`.
- Start classifier with OSC enabled and send-prob on the machine running the UI.
- Start `music_controller.py` listening on the same OSC port, sending out to your synth/DAW bridge.
- Launch UI:
  - Dev: `npm run dev` in `ui/`
  - Prod: `npm run build` then `npm start`
- Navigate Home → Setup (check LEDs) → New Session (or Dev Bypass) → Session view.

This captures the system as it stands: a functional pipeline from EEG to music, with a modern UI, reliable status/messaging, and persistent session logging.

---

## ✅ SYSTEM INTEGRATION COMPLETE

**The BCI Music Generation System is now fully integrated and operational!**

### Quick Start
```bash
# Interactive startup (recommended)
python start_system.py

# OR direct launch
python main.py --mode full
```

### System Status: 🟢 OPERATIONAL
- ✅ All components bridged and communicating
- ✅ OSC message routing implemented
- ✅ Audio synthesis pipeline working
- ✅ UI integration complete
- ✅ Session logging functional
- ✅ Demo mode available (no hardware required)

### Key Integration Features
1. **Unified Launcher**: Single entry point for all system modes
2. **Audio Bridge**: Seamless connection between music controller and audio engine
3. **OSC Communication**: All components communicate via standardized OSC messages
4. **Flexible Deployment**: Run individual components or complete system
5. **Hardware Optional**: Demo mode works without EEG hardware

### Architecture Overview
```
🧠 EEG → 📡 Classifier → 🎵 Controller → 🔗 Bridge → 🔊 Audio → 🎧 Output
                           ↓
                        🖥️ UI (Monitor & Control)
```

See **INTEGRATION_GUIDE.md** for detailed setup and usage instructions.