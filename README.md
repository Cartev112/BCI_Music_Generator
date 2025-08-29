# BCI Music Generator 

A real-time Brain-Computer Interface system that generates music from EEG signals using machine learning and adaptive harmonization algorithms.

## Features

- **Real-time EEG Processing**: Classifies mental states (rest/imagery) from 4-channel EEG data
- **Adaptive Music Generation**: Dynamic chord progressions and arpeggios based on brain activity
- **Modern UI**: React/Electron interface with real-time EEG monitoring and music controls
- **Session Logging**: SQLite database for tracking musical sessions and brain data
- **Demo Mode**: Test the system without EEG hardware

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
cd ui && npm install && cd ..

# Start the full system
python start_system.py

# OR start individual components
python main.py --mode full    # Complete system
python main.py --mode audio   # Audio engine only
python main.py --mode demo    # Demo without hardware
```

## System Architecture

```
🧠 EEG → 📡 Classifier → 🎵 Controller → 🔊 Audio → 🎧 Output
                           ↓
                        🖥️ UI (Monitor & Control)
```

## Hardware Requirements

- **EEG Device**: OpenBCI Ganglion Board (4 channels)
- **Electrodes**: O1, O2 (occipital) or P3, P4 (parietal) placement
- **Audio**: Standard audio output device

## Software Requirements

- Python 3.8+
- Node.js 16+
- Audio drivers (ASIO recommended for low latency)

## Usage

1. **Setup**: Connect EEG hardware and run `python start_system.py`
2. **Calibration**: Train a classifier with your brain data
3. **Session**: Use the UI to monitor EEG and control music parameters
4. **Analysis**: Review session data and musical outputs

## Development

- **UI Development**: `cd ui && npm run dev`
- **Testing**: `python test_integration.py`
- **Documentation**: See `INTEGRATION_GUIDE.md` for detailed setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

*Transform your thoughts into music with the power of brain-computer interfaces!*
