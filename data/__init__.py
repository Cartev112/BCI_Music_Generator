"""
BCI Music Generator - Data Processing Module

This module contains EEG data processing and analysis components:
- Data acquisition from BCI devices
- Feature extraction and analysis
- Offline analysis tools
- Advanced EEG metrics
"""

try:
    from .features import compute_epoch_features, compute_channel_features
    
    __all__ = ['compute_epoch_features', 'compute_channel_features']
except ImportError:
    # Allow module to be imported even if some dependencies are missing
    __all__ = []

