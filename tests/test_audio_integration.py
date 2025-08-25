#!/usr/bin/env python3
"""
Quick integration test for the BCI Audio Engine
Tests OSC message handling without requiring actual audio hardware
"""

import time
import threading
from pythonosc import udp_client
from audio_engine import BCIAudioEngine


def test_audio_engine():
    """Test the audio engine with simulated OSC messages"""
    
    print("🧪 Testing BCI Audio Engine Integration...")
    
    # Create engine (won't start audio server in test mode)
    engine = BCIAudioEngine(listen_port=9002)  # Different port to avoid conflicts
    
    # Setup OSC only (no audio for testing)
    engine.setup_osc_server()
    engine.start_osc_server()
    
    # Give server time to start
    time.sleep(0.5)
    
    # Create OSC client to send test messages
    client = udp_client.SimpleUDPClient("127.0.0.1", 9002)
    
    print("📤 Sending test OSC messages...")
    
    # Test chord message (like from music_controller.py)
    client.send_message("/music/chord", [0, "maj", 0.3, 60, 64, 67])  # C major, 30% probability
    time.sleep(0.1)
    
    # Test BCI probability updates
    for prob in [0.0, 0.2, 0.5, 0.8, 1.0]:
        client.send_message("/bci/prob_img", prob)
        time.sleep(0.2)
    
    # Test BCI state changes
    client.send_message("/bci/state", 0)  # REST
    time.sleep(0.2)
    client.send_message("/bci/state", 1)  # IMAGERY
    time.sleep(0.2)
    
    # Test individual notes
    client.send_message("/music/note", [64, 90])  # E note, velocity 90
    client.send_message("/music/note", [67, 80])  # G note, velocity 80
    
    print("✅ Test messages sent successfully!")
    print("📊 Check console output above for message handling confirmation")
    
    # Cleanup
    time.sleep(1)
    if engine.osc_server:
        engine.osc_server.shutdown()
    
    print("🎯 Integration test completed!")


def simulate_music_controller():
    """Simulate the music controller sending realistic chord progressions"""
    
    print("🎼 Simulating Music Controller chord progression...")
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 9001)  # Default audio engine port
    
    # Simulate a simple chord progression with varying BCI probabilities
    chords = [
        (0, "maj", [60, 64, 67]),    # C major
        (5, "min", [65, 68, 72]),    # F minor  
        (7, "7", [67, 71, 74, 77]),  # G7
        (0, "maj", [60, 64, 67]),    # C major
    ]
    
    probabilities = [0.1, 0.4, 0.8, 0.3]  # Varying mental imagery confidence
    
    for i, ((root, quality, pitches), prob) in enumerate(zip(chords, probabilities)):
        print(f"🎵 Chord {i+1}: {root} {quality} (prob: {prob})")
        
        # Send chord
        client.send_message("/music/chord", [root, quality, prob] + pitches)
        
        # Send BCI updates
        client.send_message("/bci/prob_img", prob)
        client.send_message("/bci/state", 1 if prob > 0.5 else 0)
        
        # Send some arpeggiated notes
        for pitch in pitches:
            client.send_message("/music/note", [pitch, 70 + int(prob * 20)])
            time.sleep(0.3)
        
        time.sleep(2)  # Wait between chords


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simulate":
        print("🎹 Running simulation mode (requires audio_engine.py running separately)")
        print("   Start with: python audio_engine.py")
        print("   Then run: python test_audio_integration.py simulate")
        time.sleep(2)
        simulate_music_controller()
    else:
        test_audio_engine()
