#!/usr/bin/env python3
"""
Audio Bridge for BCI Music System

This module bridges the music controller output with the audio engine input.
It receives OSC messages from the music controller and forwards them to the audio engine.
"""

import argparse
import time
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

try:
    from audio.audio_engine import BCIAudioEngine
except ImportError:
    print("Warning: Could not import BCIAudioEngine. Running in OSC-only mode.")
    BCIAudioEngine = None


class AudioBridge:
    """Bridge between music controller and audio engine"""
    
    def __init__(self, listen_port=9001, audio_port=9002):
        self.listen_port = listen_port
        self.audio_port = audio_port
        self.running = False
        
        # OSC client to forward to audio engine
        self.audio_client = SimpleUDPClient("127.0.0.1", audio_port)
        
        # OSC dispatcher for incoming music messages
        self.dispatcher = Dispatcher()
        self.dispatcher.map("/music/chord", self.handle_chord)
        self.dispatcher.map("/music/note", self.handle_note)
        self.dispatcher.map("/bci/prob_img", self.handle_bci_prob)
        self.dispatcher.map("/bci/state", self.handle_bci_state)
        self.dispatcher.map("/system/start", self.handle_start)
        self.dispatcher.map("/system/stop", self.handle_stop)
        self.dispatcher.map("/system/pause", self.handle_pause)
        
        # OSC server
        self.server = ThreadingOSCUDPServer(("0.0.0.0", listen_port), self.dispatcher)
        
    def handle_chord(self, unused_addr, *args):
        """Handle incoming chord messages: /music/chord <root> <quality> <prob> <pitch1> <pitch2> ..."""
        if len(args) < 3:
            return
            
        root = args[0]
        quality = args[1]
        prob = float(args[2])
        pitches = [int(p) for p in args[3:] if isinstance(p, (int, float))]
        
        print(f"🎵 Chord: {root}{quality} (prob={prob:.2f}) pitches={pitches}")
        
        # Forward to audio engine using its expected format
        self.audio_client.send_message("/music/chord", [root, quality, prob] + pitches)
        
    def handle_note(self, unused_addr, pitch, velocity=90):
        """Handle incoming note messages: /music/note <pitch> <velocity>"""
        pitch = int(pitch)
        velocity = int(velocity)
        
        print(f"🎵 Note: {pitch} vel={velocity}")
        
        # Forward to audio engine
        self.audio_client.send_message("/music/note", [pitch, velocity])
    
    def handle_bci_prob(self, unused_addr, prob):
        """Handle BCI probability messages"""
        print(f"🧠 BCI Probability: {prob:.3f}")
        # Forward to audio engine
        self.audio_client.send_message("/bci/prob_img", [float(prob)])
    
    def handle_bci_state(self, unused_addr, state):
        """Handle BCI state messages"""
        print(f"🧠 BCI State: {'IMAGERY' if state else 'REST'}")
        # Forward to audio engine
        self.audio_client.send_message("/bci/state", [int(state)])
    
    def handle_start(self, unused_addr):
        """Handle system start"""
        print("🎵 System Start")
        # Could send start signal to audio engine if needed
    
    def handle_stop(self, unused_addr):
        """Handle system stop"""
        print("🎵 System Stop")
        # Could send stop signal to audio engine if needed
    
    def handle_pause(self, unused_addr):
        """Handle system pause"""
        print("🎵 System Pause")
        # Could implement pause logic here
    
    def start(self):
        """Start the audio bridge server"""
        print(f"🔗 Starting Audio Bridge on port {self.listen_port}")
        print(f"   Forwarding to audio engine on port {self.audio_port}")
        
        self.running = True
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Audio Bridge...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the audio bridge"""
        self.running = False


def main():
    """Main entry point for audio bridge"""
    parser = argparse.ArgumentParser(description="Audio Bridge for BCI Music System")
    parser.add_argument("--listen-port", type=int, default=9001, 
                       help="Port to listen for music controller OSC messages")
    parser.add_argument("--audio-port", type=int, default=9002,
                       help="Port to forward messages to audio engine")
    
    args = parser.parse_args()
    
    # Create and start bridge
    bridge = AudioBridge(listen_port=args.listen_port, audio_port=args.audio_port)
    bridge.start()


if __name__ == "__main__":
    main()
