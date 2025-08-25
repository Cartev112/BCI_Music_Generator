#!/usr/bin/env python3
"""
Simple launcher for BCI Audio Engine demo
Starts the audio engine and runs a continuous demo
"""

import time
import threading
from pythonosc import udp_client
from audio_engine import BCIAudioEngine


def run_continuous_demo():
    """Run a continuous demo with changing BCI states"""
    
    client = udp_client.SimpleUDPClient("127.0.0.1", 9001)
    
    # Demo chord progressions
    progressions = [
        # Peaceful progression (low BCI activity)
        [
            (0, "maj", [60, 64, 67], 0.1),    # C major
            (5, "maj", [65, 69, 72], 0.2),    # F major
            (0, "maj", [60, 64, 67], 0.1),    # C major
            (7, "maj", [67, 71, 74], 0.15),   # G major
        ],
        # Active progression (high BCI activity)
        [
            (0, "min", [60, 63, 67], 0.7),    # C minor
            (3, "7", [63, 67, 70, 73], 0.8),  # Eb7
            (10, "min", [70, 73, 77], 0.9),   # Bb minor
            (5, "7", [65, 69, 72, 75], 0.6),  # F7
        ],
        # Mixed progression
        [
            (2, "min", [62, 65, 69], 0.3),    # D minor
            (7, "7", [67, 71, 74, 77], 0.6),  # G7
            (0, "maj", [60, 64, 67], 0.4),    # C major
            (9, "min", [69, 72, 76], 0.5),    # A minor
        ]
    ]
    
    print("🎵 Starting continuous BCI audio demo...")
    print("   🧠 Watch BCI probability changes affect the sound")
    print("   🎹 Chord progressions will cycle automatically")
    print("   ⏹️  Press Ctrl+C to stop")
    
    try:
        cycle = 0
        while True:
            progression = progressions[cycle % len(progressions)]
            
            print(f"\n🔄 Cycle {cycle + 1} - Progression {(cycle % len(progressions)) + 1}")
            
            for i, (root, quality, pitches, prob) in enumerate(progression):
                # Send chord
                client.send_message("/music/chord", [root, quality, prob] + pitches)
                
                # Send BCI state
                state = 1 if prob > 0.5 else 0
                client.send_message("/bci/prob_img", prob)
                client.send_message("/bci/state", state)
                
                state_name = "IMAGERY" if state else "REST"
                print(f"  🎵 {root} {quality} | BCI: {prob:.1f} ({state_name})")
                
                # Send individual notes for arpeggio
                for pitch in pitches:
                    client.send_message("/music/note", [pitch, int(70 + prob * 20)])
                    time.sleep(0.2)
                
                # Wait between chords
                time.sleep(3)
            
            cycle += 1
            time.sleep(1)  # Brief pause between progressions
            
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")


def main():
    """Main demo launcher"""
    print("🎼 BCI Audio Engine Demo Launcher")
    print("=" * 50)
    
    # Create and start audio engine
    engine = BCIAudioEngine(listen_port=9001)
    
    try:
        print("🔊 Starting audio engine...")
        engine.start_audio()
        
        print("📡 Starting OSC server...")
        engine.setup_osc_server()
        engine.start_osc_server()
        
        # Give everything time to start
        time.sleep(1)
        
        print("✅ Audio engine ready!")
        print("\n🎮 Demo Options:")
        print("   1. Continuous demo (automatic chord progressions)")
        print("   2. Interactive mode (manual control)")
        print("   3. Single test (quick test and exit)")
        
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            run_continuous_demo()
        elif choice == "2":
            print("\n🎮 Interactive Mode")
            print("Commands: p <prob>, s <state>, c (C maj), f (F min), g (G7), q (quit)")
            
            client = udp_client.SimpleUDPClient("127.0.0.1", 9001)
            
            while True:
                try:
                    cmd = input("> ").strip().lower()
                    if cmd == 'q':
                        break
                    elif cmd.startswith('p '):
                        prob = float(cmd[2:])
                        client.send_message("/bci/prob_img", prob)
                        print(f"📡 BCI probability: {prob}")
                    elif cmd.startswith('s '):
                        state = int(cmd[2:])
                        client.send_message("/bci/state", state)
                        print(f"📡 BCI state: {'IMAGERY' if state else 'REST'}")
                    elif cmd == 'c':
                        client.send_message("/music/chord", [0, "maj", 0.5, 60, 64, 67])
                        print("📡 C major chord")
                    elif cmd == 'f':
                        client.send_message("/music/chord", [5, "min", 0.3, 65, 68, 72])
                        print("📡 F minor chord")
                    elif cmd == 'g':
                        client.send_message("/music/chord", [7, "7", 0.8, 67, 71, 74, 77])
                        print("📡 G7 chord")
                except (ValueError, KeyboardInterrupt):
                    break
                    
        elif choice == "3":
            print("\n🧪 Running quick test...")
            client = udp_client.SimpleUDPClient("127.0.0.1", 9001)
            
            # Quick test sequence
            test_sequence = [
                (0.0, "REST - Pure ambient pad"),
                (0.3, "Light imagery"),
                (0.6, "Moderate imagery"),
                (0.9, "Strong imagery"),
                (0.0, "Back to REST")
            ]
            
            for prob, description in test_sequence:
                print(f"🧠 {description} (prob: {prob})")
                client.send_message("/bci/prob_img", prob)
                client.send_message("/bci/state", 1 if prob > 0.5 else 0)
                client.send_message("/music/chord", [0, "maj", prob, 60, 64, 67])
                time.sleep(2)
            
            print("✅ Test completed!")
        
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        print("\n🛑 Shutting down...")
        engine.stop_audio()
        if engine.osc_server:
            engine.osc_server.shutdown()


if __name__ == "__main__":
    main()
