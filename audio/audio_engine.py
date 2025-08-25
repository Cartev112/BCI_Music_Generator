#!/usr/bin/env python3
"""
Simple Audio Engine for BCI Music Generator
Uses sounddevice + numpy for Windows-compatible real-time synthesis
"""

import time
import threading
import numpy as np
from typing import Dict, List, Optional
import sounddevice as sd
from pythonosc import dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


class BCIAudioEngine:
    """
    Real-time audio synthesis engine for BCI music generation.
    
    Features:
    - REST state: Warm ambient pad with slow evolution
    - IMAGERY state: Bright arpeggiated melody
    - Real-time crossfading based on BCI probability
    - OSC control integration
    - Windows-compatible (no compilation required)
    """
    
    def __init__(self, listen_port: int = 9001, sample_rate: int = 44100, block_size: int = 512):
        # Audio settings
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = 2  # Stereo
        
        # Synthesis state
        self.current_chord: List[int] = [60, 64, 67]  # C major default
        self.bci_probability: float = 0.0
        self.bci_state: int = 0  # 0=REST, 1=IMAGERY
        
        # Audio synthesis parameters
        self.phase_pad = np.zeros(3)  # Phase for pad oscillators
        self.phase_arp = 0.0  # Phase for arpeggio
        self.arp_index = 0  # Current arp note index
        self.arp_timer = 0  # Arp timing counter
        self.arp_rate = 4.0  # Notes per second
        self.last_arp_note = None  # Track note changes for phase reset
        
        # Control parameters (smoothed)
        self.pad_volume = 0.8
        self.pad_volume_target = 0.8
        self.arp_volume = 0.0
        self.arp_volume_target = 0.0
        self.filter_cutoff = 8000.0  # Start with minimal filtering
        self.filter_cutoff_target = 8000.0
        
        # Filter state (simple lowpass)
        self.filter_state = np.zeros(2)
        
        # Shutdown flag for clean audio stop
        self.shutting_down = False
        
        # OSC setup
        self.listen_port = listen_port
        self.osc_server = None
        
        # Audio stream
        self.stream = None
        self.running = False
        
        print(f"🎵 BCI Audio Engine initialized (SR: {sample_rate}, Block: {block_size})")
    
    def _midi_to_freq(self, midi_note: int) -> float:
        """Convert MIDI note to frequency"""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
    def _smooth_parameter(self, current: float, target: float, smoothing: float = 0.99) -> float:
        """Smooth parameter changes to avoid clicks"""
        return current * smoothing + target * (1.0 - smoothing)
    
    def _generate_pad_layer(self, frames: int) -> np.ndarray:
        """Generate ambient pad layer (REST state) - fixed oscillation issues"""
        if self.pad_volume < 0.001:
            return np.zeros((frames, 2))
        
        # Get frequencies for current chord
        freqs = [self._midi_to_freq(note) for note in self.current_chord[:3]]  # Max 3 notes
        
        # Generate clean oscillators per note
        audio = np.zeros((frames, 2))
        
        for i, freq in enumerate(freqs):
            if i >= len(self.phase_pad):
                break
                
            # Calculate phase increment
            phase_inc = 2 * np.pi * freq / self.sample_rate
            
            # Generate phase array for this block
            phase_start = self.phase_pad[i]
            phase_indices = np.arange(frames)
            phases = phase_start + phase_indices * phase_inc
            
            # Generate clean sine wave (no detuning to eliminate beating)
            wave = np.sin(phases) * 0.2
            
            # Add subtle harmonic for richness (octave relationship, no beating)
            harmonic = np.sin(phases * 2.0) * 0.05  # Perfect octave, no detuning
            
            # Combine waves
            combined = wave + harmonic
            
            # Fixed panning calculation (prevent negative values)
            pan_positions = [0.5, 0.2, 0.8]  # Center, left, right
            pan = pan_positions[i] if i < len(pan_positions) else 0.5
            pan = np.clip(pan, 0.0, 1.0)  # Ensure valid range
            
            left_gain = np.sqrt(1.0 - pan)
            right_gain = np.sqrt(pan)
            
            audio[:, 0] += combined * left_gain
            audio[:, 1] += combined * right_gain
            
            # Update phase for continuity (keep in reasonable range)
            self.phase_pad[i] = (phase_start + frames * phase_inc) % (2 * np.pi)
        
        # Apply volume
        audio *= self.pad_volume
        
        return audio
    
    def _generate_arp_layer(self, frames: int) -> np.ndarray:
        """Generate clean arpeggiated melody layer (IMAGERY state)"""
        if self.arp_volume < 0.001:
            return np.zeros((frames, 2))
        
        audio = np.zeros((frames, 2))
        
        # Arpeggio timing
        samples_per_note = int(self.sample_rate / self.arp_rate)
        
        # Process in chunks for efficiency and smoothness
        i = 0
        while i < frames:
            # Check if we should advance to next arp note
            if self.arp_timer >= samples_per_note:
                self.arp_index = (self.arp_index + 1) % len(self.current_chord)
                self.arp_timer = 0
            
            # Get current arp note frequency
            current_note = self.current_chord[self.arp_index]
            freq = self._midi_to_freq(current_note) * 2.0
            
            # Calculate how many samples to generate for this note
            samples_remaining_this_note = samples_per_note - self.arp_timer
            samples_to_generate = min(samples_remaining_this_note, frames - i)
            
            # Generate clean sine wave (no FM to avoid harshness)
            phase_start = self.phase_arp
            phase_inc = 2 * np.pi * freq / self.sample_rate
            
            # Generate phase array for this chunk
            phase_indices = np.arange(samples_to_generate)
            phases = phase_start + phase_indices * phase_inc
            
            # Clean sine wave with subtle harmonic for brightness
            fundamental = np.sin(phases) * 0.3
            harmonic = np.sin(phases * 2.0) * 0.1  # Octave harmonic
            wave = fundamental + harmonic
            
            # Smooth envelope for each note
            note_progress_start = self.arp_timer / samples_per_note
            note_progress_end = (self.arp_timer + samples_to_generate) / samples_per_note
            
            # Create envelope for this chunk
            progress_array = np.linspace(note_progress_start, note_progress_end, samples_to_generate)
            envelope = np.ones_like(progress_array)
            
            # Attack phase (first 10%)
            attack_mask = progress_array < 0.1
            envelope[attack_mask] = progress_array[attack_mask] / 0.1
            
            # Decay phase (last 20%)
            decay_mask = progress_array > 0.8
            envelope[decay_mask] = (1.0 - progress_array[decay_mask]) / 0.2
            
            # Apply envelope
            wave *= envelope
            
            # Add to output with stereo spread
            audio[i:i+samples_to_generate, 0] = wave * 0.8  # Left
            audio[i:i+samples_to_generate, 1] = wave * 0.6  # Right (less dominant)
            
            # Update counters
            self.phase_arp = (phase_start + samples_to_generate * phase_inc) % (2 * np.pi)
            self.arp_timer += samples_to_generate
            i += samples_to_generate
        
        # Apply volume
        audio *= self.arp_volume
        
        return audio
    
    def _apply_filter(self, audio: np.ndarray) -> np.ndarray:
        """Apply simple lowpass filter with improved stability"""
        if self.filter_cutoff >= self.sample_rate * 0.4:
            return audio  # No filtering needed
        
        # Simple one-pole lowpass filter with better coefficient calculation
        cutoff_norm = self.filter_cutoff / (self.sample_rate * 0.5)
        cutoff_norm = np.clip(cutoff_norm, 0.01, 0.99)
        
        # Improved filter coefficient calculation
        alpha = np.exp(-2 * np.pi * cutoff_norm * 0.5)  # More stable
        
        filtered = np.zeros_like(audio)
        
        for ch in range(audio.shape[1]):
            for i in range(audio.shape[0]):
                # Add small epsilon to prevent denormal numbers
                input_sample = audio[i, ch] + 1e-10
                self.filter_state[ch] = alpha * self.filter_state[ch] + (1 - alpha) * input_sample
                filtered[i, ch] = self.filter_state[ch] - 1e-10  # Remove epsilon
        
        return filtered
    
    def _audio_callback(self, outdata: np.ndarray, frames: int, time, status):
        """Audio callback function called by sounddevice"""
        if status:
            print(f"Audio callback status: {status}")
        
        # If shutting down, output silence to prevent frozen audio
        if self.shutting_down:
            outdata.fill(0)
            return
        
        try:
            # Smooth parameter changes
            self.pad_volume = self._smooth_parameter(self.pad_volume, self.pad_volume_target)
            self.arp_volume = self._smooth_parameter(self.arp_volume, self.arp_volume_target)
            self.filter_cutoff = self._smooth_parameter(self.filter_cutoff, self.filter_cutoff_target)
            
            # Generate synthesis layers
            pad_audio = self._generate_pad_layer(frames)
            arp_audio = self._generate_arp_layer(frames)
            
            # Mix layers
            mixed = pad_audio + arp_audio
            
            # Apply global filter
            filtered = self._apply_filter(mixed)
            
            # Apply master volume and light compression
            master_volume = 0.7
            filtered *= master_volume
            
            # Simple soft clipping to prevent distortion
            filtered = np.tanh(filtered * 0.8) * 1.25
            
            # Output to soundcard
            outdata[:] = filtered
            
        except Exception as e:
            print(f"Audio callback error: {e}")
            import traceback
            traceback.print_exc()
            outdata.fill(0)  # Output silence on error to prevent noise
    
    def start_audio(self):
        """Start the audio stream"""
        try:
            # List available audio devices (for debugging)
            devices = sd.query_devices()
            print(f"🔊 Available audio devices: {len(devices)} found")
            
            # Start audio stream
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=self.channels,
                callback=self._audio_callback,
                dtype=np.float32
            )
            
            self.stream.start()
            self.running = True
            print("🎵 Audio stream started successfully!")
            
        except Exception as e:
            print(f"❌ Failed to start audio: {e}")
            print("💡 Try: pip install sounddevice soundfile")
    
    def stop_audio(self):
        """Stop the audio stream with clean shutdown"""
        if self.stream and self.running:
            # Set shutdown flag to prevent audio artifacts
            self.shutting_down = True
            
            # Give audio callback time to output silence
            time.sleep(0.1)
            
            # Stop and close stream
            self.stream.stop()
            self.stream.close()
            
            # Reset synthesis state
            self.phase_pad = np.zeros(3)
            self.phase_arp = 0.0
            self.filter_state = np.zeros(2)
            self.arp_timer = 0
            self.arp_index = 0
            self.last_arp_note = None
            
            self.running = False
            self.shutting_down = False
            print("🔇 Audio stream stopped cleanly")
    
    def setup_osc_server(self):
        """Setup OSC message handlers"""
        disp = dispatcher.Dispatcher()
        
        # Chord updates from music controller
        disp.map("/music/chord", self._handle_chord)
        
        # Individual notes (for arpeggio enhancement)
        disp.map("/music/note", self._handle_note)
        
        # BCI state updates
        disp.map("/bci/prob_img", self._handle_bci_probability)
        disp.map("/bci/state", self._handle_bci_state)
        
        # Audio parameter controls
        disp.map("/audio/pad_volume", self._handle_pad_volume)
        disp.map("/audio/arp_volume", self._handle_arp_volume)
        disp.map("/audio/filter", self._handle_filter)
        
        self.osc_server = ThreadingOSCUDPServer(("127.0.0.1", self.listen_port), disp)
        print(f"🎛️  OSC server listening on port {self.listen_port}")
    
    def start_osc_server(self):
        """Start OSC server in background thread"""
        if self.osc_server:
            server_thread = threading.Thread(target=self.osc_server.serve_forever, daemon=True)
            server_thread.start()
            print("📡 OSC server started")
    
    def _handle_chord(self, address, *args):
        """Handle /music/chord messages: root, quality, prob, pitch1, pitch2, ..."""
        if len(args) >= 4:
            root, quality, prob = args[0], args[1], args[2]
            pitches = list(args[3:])
            
            self.current_chord = pitches
            print(f"🎵 Chord updated: {root} {quality} (prob: {prob:.2f}) -> {pitches}")
    
    def _handle_note(self, address, *args):
        """Handle /music/note messages for individual notes"""
        if len(args) >= 2:
            pitch, velocity = args[0], args[1]
            print(f"🎶 Note: {pitch} vel:{velocity}")
    
    def _handle_bci_probability(self, address, prob_img):
        """Handle BCI probability updates"""
        self.bci_probability = float(prob_img)
        
        # Crossfade layers based on probability
        # REST (pad) dominant when prob is low
        # IMAGERY (arp) dominant when prob is high
        self.pad_volume_target = 0.8 * (1.0 - self.bci_probability)
        self.arp_volume_target = 0.6 * self.bci_probability
        
        # Brightness increases with probability (more conservative range)
        self.filter_cutoff_target = 2000 + (self.bci_probability * 6000)  # 2000-8000 Hz range
        
        print(f"🧠 BCI prob: {prob_img:.2f} -> Pad:{self.pad_volume_target:.2f} Arp:{self.arp_volume_target:.2f} Filter:{self.filter_cutoff_target:.0f}Hz")
    
    def _handle_bci_state(self, address, state):
        """Handle discrete BCI state changes"""
        self.bci_state = int(state)
        
        if self.bci_state == 0:  # REST
            # Slower arpeggio
            self.arp_rate = 2.0
        else:  # IMAGERY
            # Faster arpeggio
            self.arp_rate = 6.0
        
        print(f"🧠 BCI state: {'IMAGERY' if state else 'REST'} (arp rate: {self.arp_rate} Hz)")
    
    def _handle_pad_volume(self, address, volume):
        """Manual pad volume control"""
        self.pad_volume_target = float(volume)
    
    def _handle_arp_volume(self, address, volume):
        """Manual arp volume control"""
        self.arp_volume_target = float(volume)
    
    def _handle_filter(self, address, cutoff):
        """Manual filter control"""
        self.filter_cutoff_target = float(cutoff)


def main():
    """Main entry point for standalone testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BCI Audio Engine")
    parser.add_argument("--port", type=int, default=9001, help="OSC listen port")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Audio sample rate")
    parser.add_argument("--block-size", type=int, default=512, help="Audio block size")
    args = parser.parse_args()
    
    # Create and start engine
    engine = BCIAudioEngine(
        listen_port=args.port,
        sample_rate=args.sample_rate,
        block_size=args.block_size
    )
    
    try:
        # Start audio
        engine.start_audio()
        
        # Start OSC server
        engine.setup_osc_server()
        engine.start_osc_server()
        
        print("🚀 BCI Audio Engine running! Press Ctrl+C to stop...")
        print("   Listening for OSC messages on port", args.port)
        print("   Expected messages:")
        print("     /music/chord <root> <quality> <prob> <pitch1> <pitch2> ...")
        print("     /bci/prob_img <probability>")
        print("     /bci/state <0|1>")
        print("\n💡 Test the engine:")
        print("   1. You should hear a quiet ambient pad")
        print("   2. Send BCI messages to hear the layers change")
        print("   3. Use test_audio_integration.py for automated testing")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        
        # Clean shutdown sequence
        try:
            engine.stop_audio()
        except Exception as e:
            print(f"Error stopping audio: {e}")
        
        try:
            if engine.osc_server:
                engine.osc_server.shutdown()
        except Exception as e:
            print(f"Error stopping OSC server: {e}")
        
        print("👋 Shutdown complete")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        # Emergency shutdown
        try:
            engine.stop_audio()
        except:
            pass
        try:
            if engine.osc_server:
                engine.osc_server.shutdown()
        except:
            pass


if __name__ == "__main__":
    main()