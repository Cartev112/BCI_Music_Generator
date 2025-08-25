"""
BCI Music Generator - Audio Processing Module

This module contains the audio synthesis and music generation components:
- Audio engine for real-time synthesis
- Adaptive harmonization
- Tension-based harmonization
- Rhythm generation
"""

try:
    from .audio_engine import BCIAudioEngine
    from .adaptive_harmonizer import AdaptiveTensionHarmonizer
    from .tension_harmonizer import TensionHarmonizer
    from .rhythm_engine import Arpeggiator
    
    __all__ = ['BCIAudioEngine', 'AdaptiveTensionHarmonizer', 'TensionHarmonizer', 'Arpeggiator']
except ImportError:
    # Allow module to be imported even if some dependencies are missing
    __all__ = []

