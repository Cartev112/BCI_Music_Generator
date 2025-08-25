#!/usr/bin/env python3
"""
Quick integration test for the BCI Audio Engine
Tests OSC message handling and provides simulation modes
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
        print(f"  Testing BCI probability: {prob}")
        client.send_message("/bci/prob_img", prob)
        time.sleep(0.2)
    
    # Test BCI state changes
    print("  Testing BCI state changes...")
    client.send_message("/bci/state", 0)  # REST
    time.sleep(0.2)
    client.send_message("/bci/state", 1)  # IMAGERY
    time.sleep(0.2)
    
    # Test individual notes
    print("  Testing individual notes...")
    client.send_message("/music/note", [64, 90])  # E note, velocity 90
    client.send_message("/music/note", [67, 80])  # G note, velocity 80
    
    # Test manual audio controls
    print("  Testing manual controls...")
    client.send_message("/audio/pad_volume", 0.5)
    client.send_message("/audio/arp_volume", 0.8)
    client.send_message("/audio/filter", 1500)
    
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
    print("   Make sure audio_engine.py is running first!")
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 9001)  # Default audio engine port
    
    # Simulate a simple chord progression with varying BCI probabilities
    chords = [
        (0, "maj", [60, 64, 67]),    # C major
        (5, "min", [65, 68, 72]),    # F minor  
        (7, "7", [67, 71, 74, 77]),  # G7
        (0, "maj", [60, 64, 67]),    # C major
    ]
    
    probabilities = [0.1, 0.4, 0.8, 0.3]  # Varying mental imagery confidence
    
    print("🎵 Starting chord progression simulation...")
    
    for i, ((root, quality, pitches), prob) in enumerate(zip(chords, probabilities)):
        print(f"🎵 Chord {i+1}/4: {root} {quality} (BCI prob: {prob})")
        
        # Send chord
        client.send_message("/music/chord", [root, quality, prob] + pitches)
        
        # Send BCI updates
        client.send_message("/bci/prob_img", prob)
        client.send_message("/bci/state", 1 if prob > 0.5 else 0)
        
        # Send some arpeggiated notes
        for j, pitch in enumerate(pitches):
            velocity = 70 + int(prob * 20)
            print(f"  🎶 Note {j+1}: {pitch} (vel: {velocity})")
            client.send_message("/music/note", [pitch, velocity])
            time.sleep(0.3)
        
        time.sleep(2)  # Wait between chords
    
    print("🎯 Chord progression simulation completed!")


def interactive_test():
    """Interactive test mode for manual control"""
    
    print("🎮 Interactive Test Mode")
    print("   Make sure audio_engine.py is running first!")
    print("   Commands:")
    print("     p <0.0-1.0> - Set BCI probability")
    print("     s <0|1>     - Set BCI state (0=REST, 1=IMAGERY)")
    print("     c           - Send C major chord")
    print("     f           - Send F minor chord")
    print("     g           - Send G7 chord")
    print("     q           - Quit")
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 9001)
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd.startswith('p '):
                prob = float(cmd[2:])
                client.send_message("/bci/prob_img", prob)
                print(f"📡 Sent BCI probability: {prob}")
            elif cmd.startswith('s '):
                state = int(cmd[2:])
                client.send_message("/bci/state", state)
                print(f"📡 Sent BCI state: {'IMAGERY' if state else 'REST'}")
            elif cmd == 'c':
                client.send_message("/music/chord", [0, "maj", 0.5, 60, 64, 67])
                print("📡 Sent C major chord")
            elif cmd == 'f':
                client.send_message("/music/chord", [5, "min", 0.3, 65, 68, 72])
                print("📡 Sent F minor chord")
            elif cmd == 'g':
                client.send_message("/music/chord", [7, "7", 0.8, 67, 71, 74, 77])
                print("📡 Sent G7 chord")
            else:
                print("❓ Unknown command. Type 'q' to quit.")
                
        except (ValueError, IndexError):
            print("❌ Invalid command format")
        except KeyboardInterrupt:
            break
    
    print("👋 Interactive test ended")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "simulate":
            simulate_music_controller()
        elif mode == "interactive" or mode == "i":
            interactive_test()
        else:
            print("❓ Unknown mode. Available modes:")
            print("   python test_audio_integration.py           # Basic test")
            print("   python test_audio_integration.py simulate  # Chord progression")
            print("   python test_audio_integration.py interactive # Manual control")
    else:
        test_audio_engine()