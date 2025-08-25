# BCI Music System Integration Guide

## Overview

The BCI Music Generation System has been successfully integrated! All components are now properly bridged and can work together as a complete pipeline.

## System Architecture

```
🧠 EEG Hardware → 📡 Real-time Classifier → 🎵 Music Controller → 🔗 Audio Bridge → 🔊 Audio Engine
                                    ↓
                                 🖥️ UI (Monitor & Control)
```

## Components

### 1. Real-time Classifier (`core/real_time_classifier.py`)
- **Purpose**: Processes live EEG data and classifies mental states
- **Input**: EEG signals from Ganglion board
- **Output**: OSC messages with BCI state and probability
- **Port**: Sends to 9000

### 2. Music Controller (`core/music_controller.py`)
- **Purpose**: Generates musical content based on BCI state
- **Input**: BCI probability/state via OSC
- **Output**: Chord progressions and arpeggios via OSC
- **Ports**: Listens on 9000, sends to 9001

### 3. Audio Bridge (`core/audio_bridge.py`)
- **Purpose**: Forwards music data to audio engine
- **Input**: Music messages from controller
- **Output**: Forwards to audio engine
- **Ports**: Listens on 9001, sends to 9002

### 4. Audio Engine (`audio/audio_engine.py`)
- **Purpose**: Real-time audio synthesis
- **Input**: Music data via OSC
- **Output**: Audio to speakers/headphones
- **Port**: Listens on 9002

### 5. UI (`ui/`)
- **Purpose**: Monitoring, control, and visualization
- **Features**: EEG monitoring, music controls, session history
- **Ports**: Monitors 9000, controls via 9001

## Quick Start

### Option 1: Full System (Recommended)
```bash
python start_system.py
# Follow the interactive prompts
```

### Option 2: Manual Launch
```bash
# Full system with hardware
python main.py --mode full --serial-port COM3 --model-path model.joblib

# Demo mode (no hardware)
python main.py --mode full
```

### Option 3: Individual Components
```bash
# Audio engine only
python main.py --mode audio

# Music controller only
python main.py --mode controller

# UI only
python main.py --mode ui
```

## OSC Message Flow

### From Classifier to Controller
- `/bci/prob_img <float>` - Imagery probability (0.0-1.0)
- `/bci/state <int>` - Mental state (0=REST, 1=IMAGERY)
- `/status/board <1|0>` - Hardware status
- `/status/classifier <1|0>` - Classifier status
- `/status/osc <1|0>` - OSC status

### From Controller to Bridge
- `/music/chord <root> <quality> <prob> <pitch1> <pitch2> ...`
- `/music/note <pitch> <velocity>`

### From Bridge to Audio Engine
- `/music/chord <root> <quality> <prob> <pitch1> <pitch2> ...`
- `/music/note <pitch> <velocity>`
- `/bci/prob_img <float>`
- `/bci/state <int>`

### From UI to Controller
- `/music/preset <name>`
- `/music/tempo <bpm>`
- `/music/key <string>`
- `/music/adaptive <0|1>`
- `/rhythm/arp_mode <mode>`
- `/system/start|stop|pause`

## Testing Without Hardware

1. **Start Demo Mode**:
   ```bash
   python start_system.py
   # Select option 2 (Demo Mode)
   ```

2. **Use Dev Bypass**: In the UI Setup page, click "Dev Bypass" to skip hardware requirements

3. **Test Audio**: The audio engine will generate ambient music that responds to simulated BCI data

## Development Workflow

### Testing Individual Components

1. **Audio Engine**:
   ```bash
   python main.py --mode audio
   # Test with: python test_audio_integration.py
   ```

2. **Music Controller**:
   ```bash
   python main.py --mode controller
   # Sends test OSC messages to port 9001
   ```

3. **UI Development**:
   ```bash
   cd ui
   npm run dev
   ```

### Adding New Features

1. **New OSC Messages**: Add handlers in the appropriate component
2. **UI Controls**: Add to `ui/src/components/MusicControls.tsx`
3. **Audio Effects**: Modify `audio/audio_engine.py`
4. **Music Algorithms**: Extend `audio/tension_harmonizer.py`

## Troubleshooting

### Common Issues

1. **Port Conflicts**: 
   - Check if ports 9000-9002 are available
   - Modify port numbers in component arguments if needed

2. **Audio Problems**:
   - Install: `pip install sounddevice soundfile`
   - Check audio device availability

3. **UI Not Loading**:
   - Run `npm install` in ui/ directory
   - Check Node.js version (requires 16+)

4. **Import Errors**:
   - Ensure all dependencies installed: `pip install -r requirements.txt`
   - Check Python path includes project directories

### Debug Mode

Enable verbose logging:
```bash
python main.py --mode full --verbose
```

## System Requirements

### Hardware
- OpenBCI Ganglion board (optional for demo)
- Audio output device
- 4+ GB RAM

### Software
- Python 3.8+
- Node.js 16+
- Required Python packages (see requirements.txt)
- Required npm packages (see ui/package.json)

## Next Steps

1. **Train Your Model**: Use `data/offline_analysis.py` to train a classifier
2. **Collect Data**: Use `data/data_acquisition.py` to record EEG sessions
3. **Customize Music**: Modify presets in `config/presets.py`
4. **Extend UI**: Add new visualizations or controls

## Support

- Check logs for error messages
- Test components individually
- Use demo mode for development
- Refer to component documentation in source files

---

🎵 **Happy Brain-Computer Music Making!** 🧠🎶

