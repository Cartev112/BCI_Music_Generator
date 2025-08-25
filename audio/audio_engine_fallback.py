#!/usr/bin/env python3
"""
Fallback Audio Engine for BCI Music Generator
Uses sounddevice and numpy for cross-platform compatibility
"""

import time
import threading
import numpy as np
from typing import Dict, List, Optional
import sounddevice as sd
from pythonosc import dispatcher, osc
from pythonosc.server import osc


class BCIAudioEngineFallback:
    """
    Cross-platform audio synthesis engine for BCI music generation.
    
    Features:
    - REST state: Warm ambient pad with slow evolution
    - IMAGERY state: Bright arpeggiated melody
    - Real-time crossfading based on BCI probability
    - OSC control integration
    - Compatible with Windows, macOS, and Linux
    """
    
    def __init__(self, listen_port: int = 9001, sample_rate: int = 44100, buffer_size: int = 512):
        # Audio setup
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channels = 2
        
        # State tracking
        self.current_chord: List[int] = [60, 64, 67]  # C major default
        self.bci_probability: float = 0.0
        self.bci_state: int = 0  # 0=REST, 1=IMAGERY
        
        # Audio synthesis parameters
        self.phase_pad = np.zeros(len(self.current_chord) * 3)  # 3 oscillators per note
        self.phase_arp = 0.0
        self.arp_note_index = 0
        self.arp_timer = 0
        self.arp_note_duration = 0.25  # 4 Hz arpeggio
        
        # Control parameters (smooth transitions)
        self.pad_volume = 0.8
        self.arp_volume = 0.0
        self.filter_cutoff = 1000
        self.target_pad_volume = 0.8
        self.target_arp_volume = 0.0
        self.target_filter_cutoff = 1000
        
        # Filter state
        self.filter_state = np.zeros(2)  # Simple lowpass filter state
        
        # OSC setup
        self.listen_port = listen_port
        self.osc_server = None
        
        # Audio stream
        self.stream = None
        self.running = False
        
        print(f"🎵 BCI Audio Engine (Fallback) initialized (SR: {sample_rate}, Buffer: {buffer_size})")
    
    def _midi_to_freq(self, midi_note: int) -> float:
        """Convert MIDI note number to frequency"""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
    def _generate_pad_layer(self, frames: int) -> np.ndarray:
        """Generate warm ambient pad layer"""
        output = np.zeros((frames, self.channels))
        
        # Generate multiple detuned oscillators per chord note
        osc_idx = 0
        for note in self.current_chord:
            base_freq = self._midi_to_freq(note)
            
            # Three oscillators per note with slight detuning
            freqs = [base_freq, base_freq * 1.003, base_freq * 0.5]
            amps = [0.15, 0.12, 0.08]
            
            for freq, amp in zip(freqs, amps):
                # Generate sine wave
                phase_increment = 2 * np.pi * freq / self.sample_rate
                phases = self.phase_pad[osc_idx] + np.arange(frames) * phase_increment
                
                # Add slow LFO modulation (0.1 Hz)
                lfo_phase = time.time() * 0.1 * 2 * np.pi
                lfo_mod = 0.3 * np.sin(lfo_phase)
                
                wave = amp * np.sin(phases + lfo_mod)
                
                # Stereo spread
                output[:, 0] += wave * (0.7 + 0.3 * np.sin(osc_idx))
                output[:, 1] += wave * (0.7 + 0.3 * np.cos(osc_idx))
                
                # Update phase
                self.phase_pad[osc_idx] = phases[-1] % (2 * np.pi)
                osc_idx += 1
        
        # Simple lowpass filter simulation
        cutoff_norm = self.filter_cutoff / (self.sample_rate / 2)
        alpha = min(cutoff_norm, 0.99)
        
        for i in range(frames):
            for ch in range(self.channels):
                self.filter_state[ch] = alpha * output[i, ch] + (1 - alpha) * self.filter_state[ch]
                output[i, ch] = self.filter_state[ch]
        
        return output * self.pad_volume
    
    def _generate_arp_layer(self, frames: int) -> np.ndarray:
        """Generate bright arpeggiated melody layer"""
        output = np.zeros((frames, self.channels))
        
        if self.arp_volume <= 0.01:
            return output
        
        samples_per_note = int(self.arp_note_duration * self.sample_rate)
        
        for i in range(frames):
            # Check if we need to advance to next note
            if self.arp_timer >= samples_per_note:
                self.arp_timer = 0
                self.arp_note_index = (self.arp_note_index + 1) % len(self.current_chord)
            
            # Get current note frequency
            current_note = self.current_chord[self.arp_note_index]
            base_freq = self._midi_to_freq(current_note)
            
            # FM synthesis for brightness
            carrier_freq = base_freq
            modulator_freq = base_freq * 2.1
            mod_index = 0.3
            
            # Generate FM synthesis
            mod_phase_increment = 2 * np.pi * modulator_freq / self.sample_rate
            car_phase_increment = 2 * np.pi * carrier_freq / self.sample_rate
            
            modulator = mod_index * carrier_freq * np.sin(self.phase_arp * modulator_freq / carrier_freq)
            carrier_phase = self.phase_arp + modulator / self.sample_rate
            
            wave = 0.3 * np.sin(carrier_phase)
            
            # Envelope (attack-decay)
            note_progress = self.arp_timer / samples_per_note
            if note_progress < 0.1:  # Attack
                envelope = note_progress / 0.1
            elif note_progress < 0.3:  # Sustain
                envelope = 1.0
            else:  # Decay
                envelope = (1.0 - note_progress) / 0.7
            
            envelope = max(0, envelope)
            
            # Apply envelope and volume
            sample = wave * envelope * self.arp_volume
            
            # Stereo output
            output[i, 0] = sample
            output[i, 1] = sample
            
            # Update phases and timer
            self.phase_arp += car_phase_increment
            self.arp_timer += 1
        
        # Keep phase in reasonable range
        self.phase_arp = self.phase_arp % (2 * np.pi)
        
        return output
    
    def _audio_callback(self, outdata, frames, time, status):
        """Audio callback function for sounddevice"""
        if status:
            print(f"Audio status: {status}")
        
        try:
            # Smooth parameter transitions
            self.pad_volume += (self.target_pad_volume - self.pad_volume) * 0.01
            self.arp_volume += (self.target_arp_volume - self.arp_volume) * 0.05
            self.filter_cutoff += (self.target_filter_cutoff - self.filter_cutoff) * 0.001
            
            # Generate audio layers
            pad_audio = self._generate_pad_layer(frames)
            arp_audio = self._generate_arp_layer(frames)
            
            # Mix layers
            mixed = pad_audio + arp_audio
            
            # Prevent clipping
            mixed = np.tanh(mixed * 0.7)
            
            # Output
            outdata[:] = mixed
            
        except Exception as e:
            print(f"Audio callback error: {e}")
            outdata.fill(0)
    
    def start_audio(self):
        """Start the audio engine"""
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=self.buffer_size
            )
            self.stream.start()
            self.running = True
            print("🎵 Audio engine started successfully")
        except Exception as e:
            print(f"❌ Failed to start audio: {e}")
    
    def stop_audio(self):
        """Stop the audio engine"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("🛑 Audio engine stopped")
    
    def setup_osc(self):
        """Setup OSC message handlers"""
        disp = dispatcher.Dispatcher()
        
        # BCI state messages
        disp.map("/bci/probability", self._handle_bci_probability)
        disp.map("/bci/state", self._handle_bci_state)
        disp.map("/bci/chord", self._handle_chord_change)
        
        # Control messages
        disp.map("/control/pad_volume", self._handle_pad_volume)
        disp.map("/control/arp_volume", self._handle_arp_volume)
        disp.map("/control/filter", self._handle_filter)
        
        try:
            self.osc_server = osc.BlockingOSCUDPServer(("127.0.0.1", self.listen_port), disp)
            print(f"🎛️  OSC server listening on port {self.listen_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to setup OSC server: {e}")
            return False
    
    def _handle_bci_probability(self, unused_addr, prob):
        """Handle BCI probability updates"""
        self.bci_probability = max(0.0, min(1.0, prob))
        
        # Update volumes based on probability
        if self.bci_state == 0:  # REST state
            self.target_pad_volume = 0.8 * (1.0 - self.bci_probability * 0.3)
            self.target_arp_volume = 0.0
        else:  # IMAGERY state
            self.target_pad_volume = 0.3 * (1.0 - self.bci_probability)
            self.target_arp_volume = 0.6 * self.bci_probability
        
        # Adjust filter based on engagement
        self.target_filter_cutoff = 800 + (self.bci_probability * 1200)
    
    def _handle_bci_state(self, unused_addr, state):
        """Handle BCI state changes"""
        self.bci_state = int(state)
        print(f"🧠 BCI State: {'IMAGERY' if state else 'REST'}")
        
        # Trigger immediate parameter updates
        self._handle_bci_probability(None, self.bci_probability)
    
    def _handle_chord_change(self, unused_addr, *notes):
        """Handle chord progression changes"""
        if notes:
            self.current_chord = list(notes)
            print(f"🎵 Chord changed: {self.current_chord}")
    
    def _handle_pad_volume(self, unused_addr, volume):
        """Handle pad volume changes"""
        self.target_pad_volume = max(0.0, min(1.0, volume))
    
    def _handle_arp_volume(self, unused_addr, volume):
        """Handle arp volume changes"""
        self.target_arp_volume = max(0.0, min(1.0, volume))
    
    def _handle_filter(self, unused_addr, cutoff):
        """Handle filter cutoff changes"""
        self.target_filter_cutoff = max(100, min(8000, cutoff))
    
    def run_osc_server(self):
        """Run the OSC server in a separate thread"""
        if self.osc_server:
            print("🎛️  Starting OSC server...")
            try:
                self.osc_server.serve_forever()
            except KeyboardInterrupt:
                print("🛑 OSC server stopped")
    
    def start(self):
        """Start both audio and OSC components"""
        # Start audio
        self.start_audio()
        
        # Setup and start OSC
        if self.setup_osc():
            osc_thread = threading.Thread(target=self.run_osc_server, daemon=True)
            osc_thread.start()
            
            print("✅ BCI Audio Engine running! Send OSC messages to control audio.")
            print("   /bci/probability <float>  - Set BCI probability (0.0-1.0)")
            print("   /bci/state <int>          - Set BCI state (0=REST, 1=IMAGERY)")
            print("   /bci/chord <int> <int>... - Set chord notes (MIDI numbers)")
            
            return True
        else:
            self.stop_audio()
            return False
    
    def stop(self):
        """Stop all components"""
        if self.osc_server:
            self.osc_server.shutdown()
        self.stop_audio()


# Test function
def test_audio_engine():
    """Test the fallback audio engine"""
    engine = BCIAudioEngineFallback()
    
    if engine.start():
        try:
            print("🎵 Testing audio engine... Press Ctrl+C to stop")
            
            # Test different states
            import time
            for i in range(10):
                # Simulate BCI probability changes
                prob = 0.5 + 0.5 * np.sin(i * 0.5)
                state = 1 if prob > 0.7 else 0
                
                engine._handle_bci_probability(None, prob)
                engine._handle_bci_state(None, state)
                
                print(f"State: {'IMAGERY' if state else 'REST'}, Prob: {prob:.2f}")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
        finally:
            engine.stop()
    else:
        print("❌ Failed to start audio engine")


if __name__ == "__main__":
    test_audio_engine()

