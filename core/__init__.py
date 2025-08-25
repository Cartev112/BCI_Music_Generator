"""
BCI Music Generator - Core Processing Module

This module contains the core BCI processing components:
- Real-time EEG classification
- Feature extraction
- Music control logic  
- Session logging
"""

try:
    from .real_time_classifier import RealTimeBCI
    from .music_controller import BCIState
    from .session_logger import SessionLogger
    
    __all__ = ['RealTimeBCI', 'BCIState', 'SessionLogger']
except ImportError:
    # Allow module to be imported even if some dependencies are missing
    __all__ = []

