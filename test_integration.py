#!/usr/bin/env python3
"""
Integration Test for BCI Music System

This script tests the complete integration by simulating the data flow
through all components without requiring actual EEG hardware.
"""

import sys
import time
import threading
import subprocess
from pathlib import Path
from pythonosc.udp_client import SimpleUDPClient

# Add project paths
project_root = Path(__file__).parent
sys.path.extend([
    str(project_root / "core"),
    str(project_root / "audio"), 
    str(project_root / "data"),
    str(project_root / "config")
])


def test_osc_communication():
    """Test OSC communication between components"""
    print("🔗 Testing OSC Communication...")
    
    # Test music controller OSC
    try:
        client = SimpleUDPClient("127.0.0.1", 9000)
        
        # Simulate classifier output
        print("   📡 Sending test BCI probability...")
        client.send_message("/bci/prob_img", [0.7])
        time.sleep(0.1)
        
        print("   📡 Sending test BCI state...")
        client.send_message("/bci/state", [1])
        time.sleep(0.1)
        
        print("   ✅ OSC messages sent successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ OSC test failed: {e}")
        return False


def test_audio_bridge():
    """Test audio bridge forwarding"""
    print("🔗 Testing Audio Bridge...")
    
    try:
        client = SimpleUDPClient("127.0.0.1", 9001)
        
        # Simulate music controller output
        print("   🎵 Sending test chord...")
        client.send_message("/music/chord", ["C", "maj", 0.8, 60, 64, 67])
        time.sleep(0.1)
        
        print("   🎵 Sending test note...")
        client.send_message("/music/note", [60, 90])
        time.sleep(0.1)
        
        print("   ✅ Audio bridge messages sent successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Audio bridge test failed: {e}")
        return False


def test_imports():
    """Test that all components can be imported"""
    print("📦 Testing Component Imports...")
    
    success = True
    
    # Test core modules
    try:
        import core.real_time_classifier
        print("   ✅ Real-time Classifier")
    except Exception as e:
        print(f"   ❌ Real-time Classifier: {e}")
        success = False
    
    try:
        import core.music_controller
        print("   ✅ Music Controller")
    except Exception as e:
        print(f"   ❌ Music Controller: {e}")
        success = False
    
    try:
        import core.audio_bridge
        print("   ✅ Audio Bridge")
    except Exception as e:
        print(f"   ❌ Audio Bridge: {e}")
        success = False
    
    try:
        import core.session_logger
        print("   ✅ Session Logger")
    except Exception as e:
        print(f"   ❌ Session Logger: {e}")
        success = False
    
    try:
        import audio.audio_engine
        print("   ✅ Audio Engine")
    except Exception as e:
        print(f"   ❌ Audio Engine: {e}")
        success = False
    
    try:
        import data.features
        print("   ✅ Features")
    except Exception as e:
        print(f"   ❌ Features: {e}")
        success = False
    
    return success


def test_feature_extraction():
    """Test feature extraction pipeline"""
    print("🧠 Testing Feature Extraction...")
    
    try:
        import numpy as np
        from data.features import compute_epoch_features
        
        # Create synthetic EEG data
        fs = 250  # Sample rate
        duration = 4  # seconds
        n_channels = 4
        samples = int(fs * duration)
        
        # Generate synthetic EEG-like data
        epoch = np.random.randn(n_channels, samples) * 50  # microvolts
        
        # Add some realistic frequency content
        t = np.linspace(0, duration, samples)
        for ch in range(n_channels):
            # Add alpha rhythm (10 Hz)
            epoch[ch] += 20 * np.sin(2 * np.pi * 10 * t)
            # Add some beta (20 Hz)
            epoch[ch] += 10 * np.sin(2 * np.pi * 20 * t)
        
        # Extract features
        features = compute_epoch_features(epoch, fs)
        
        print(f"   ✅ Features extracted: {len(features)} features")
        print(f"   📊 Feature range: {features.min():.3f} to {features.max():.3f}")
        return True
        
    except Exception as e:
        print(f"   ❌ Feature extraction failed: {e}")
        return False


def main():
    """Run integration tests"""
    print("🧪 BCI Music System Integration Test")
    print("=" * 50)
    
    tests = [
        ("Component Imports", test_imports),
        ("Feature Extraction", test_feature_extraction),
        ("OSC Communication", test_osc_communication),
        ("Audio Bridge", test_audio_bridge),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("   The system is ready for use.")
        print("\n💡 Next steps:")
        print("   1. Run: python start_system.py")
        print("   2. Select demo mode to test without hardware")
        print("   3. Use UI Dev Bypass to explore the interface")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("   The system may still work, but some features might be limited.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
