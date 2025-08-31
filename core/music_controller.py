import argparse
import time
import threading
from collections import deque

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

try:
    from audio.tension_harmonizer import TensionHarmonizer, Chord, chord_to_pitches
    from audio.adaptive_harmonizer import AdaptiveTensionHarmonizer
    from audio.rhythm_engine import Arpeggiator
except ImportError:
    # Fallback imports for development
    from tension_harmonizer import TensionHarmonizer, Chord, chord_to_pitches
    from adaptive_harmonizer import AdaptiveTensionHarmonizer
    from rhythm_engine import Arpeggiator

from core.session_logger import SessionLogger

# ---------------------------
# Configurable Parameters
# ---------------------------
DEFAULT_BPM = 100
DEFAULT_BEATS_PER_CHORD = 2  # every 2 beats emit a new chord

# ---------------------------
# OSC Callbacks
# ---------------------------

class BCIState:
    def __init__(self):
        self.prob_img = 0.0
        self.state = 0
        self.lock = threading.Lock()

    def set_prob(self, unused_addr, value):
        with self.lock:
            self.prob_img = float(value)

    def set_state(self, unused_addr, value):
        with self.lock:
            self.state = int(value)

    def get_prob(self):
        with self.lock:
            return self.prob_img


# ---------------------------
# Chord Scheduler Thread
# ---------------------------

def scheduler_loop(args, bci_state: BCIState):
    client = SimpleUDPClient(args.out_ip, args.out_port)
    HarmonizerClass = AdaptiveTensionHarmonizer if args.adaptive else TensionHarmonizer
    harmonizer = HarmonizerClass(key=args.key)
    if args.preset:
        harmonizer.apply_preset(args.preset)
    current = Chord(root=0, quality="maj")

    logger = SessionLogger()
    session_id = logger.start_session(args.preset or 'consonant', args.key, args.bpm, args.beats_per_chord)

    beat_interval = 60.0 / args.bpm
    chord_interval = beat_interval * args.beats_per_chord
    arp_interval = beat_interval * args.arp_rate

    arp = Arpeggiator(mode=args.arp_mode)
    arp_next_time = time.time() + arp_interval

    next_time = time.time()
    try:
      while True:
        now = time.time()
        if now >= next_time:
            prob = bci_state.get_prob()
            next_chord = harmonizer.next_chord(current, prob)
            pitches = chord_to_pitches(next_chord, octave=args.octave)
            # Send as /music/chord <root> <quality> <prob> n pitch0 pitch1 ...
            client.send_message("/music/chord", [next_chord.root, next_chord.quality, prob] + pitches)
            logger.log_chord(next_chord.root, next_chord.quality, pitches)
            print(f"Chord: {next_chord} Prob:{prob:.2f} Pitches:{pitches}")
            current = next_chord
            arp.set_chord(pitches)
            next_time += chord_interval
        # Arpeggio notes
        if args.arp_mode != "off" and time.time() >= arp_next_time:
            pitch = arp.next_pitch()
            if pitch is not None:
                client.send_message("/music/note", [pitch, args.arp_vel])
                logger.log_note(pitch, args.arp_vel)
            arp_next_time += arp_interval
        time.sleep(0.01)
    finally:
      logger.end_session()


# ---------------------------
# Main
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Music Controller reacting to BCI probability.")
    parser.add_argument("--listen-port", type=int, default=9000, help="Port to listen for BCI OSC messages")
    parser.add_argument("--out-ip", default="127.0.0.1")
    parser.add_argument("--out-port", type=int, default=9001)
    parser.add_argument("--bpm", type=int, default=100)
    parser.add_argument("--beats-per-chord", type=int, default=2)
    parser.add_argument("--key", default="C", help="Key for harmonizer")
    parser.add_argument("--adaptive", action="store_true", help="Enable adaptive tension weights")
    parser.add_argument("--octave", type=int, default=4)
    parser.add_argument("--preset", default=None, help="Name of reharmonisation preset to apply")
    parser.add_argument("--arp-mode", default="off", help="Arpeggio mode: up,down,updown,random,off")
    parser.add_argument("--arp-rate", type=float, default=0.5, help="Arp note rate in beats")
    parser.add_argument("--arp-vel", type=int, default=90, help="MIDI velocity for arpeggiated notes")
    args = parser.parse_args()

    bci_state = BCIState()

    dispatcher = Dispatcher()
    dispatcher.map("/bci/prob_img", bci_state.set_prob)
    dispatcher.map("/bci/state", bci_state.set_state)

    def osc_preset_handler(addr, preset_name):
        try:
            harmonizer.apply_preset(str(preset_name))
            print(f"Applied preset {preset_name}")
        except ValueError as e:
            print(e)

    dispatcher.map("/music/preset", osc_preset_handler)
    # Controls from UI – update args live
    def set_bpm(addr, v):
        try:
            args.bpm = int(v)
        except Exception:
            pass
    def set_beats(addr, v):
        try:
            args.beats_per_chord = int(v)
        except Exception:
            pass
    def set_adaptive(addr, v):
        args.adaptive = bool(int(v)) if isinstance(v, (int, float, str)) else bool(v)
    def set_key(addr, v):
        try:
            args.key = str(v)
        except Exception:
            pass
    def set_arp_mode(addr, v):
        args.arp_mode = str(v)
    def set_arp_rate(addr, v):
        try:
            args.arp_rate = float(v)
        except Exception:
            pass
    def set_density(addr, v):
        try:
            args.density = float(v)
        except Exception:
            pass
    dispatcher.map("/music/tempo", set_bpm)
    dispatcher.map("/music/beats_per_chord", set_beats)
    dispatcher.map("/music/adaptive", set_adaptive)
    dispatcher.map("/music/key", set_key)
    dispatcher.map("/rhythm/arp_mode", set_arp_mode)
    dispatcher.map("/rhythm/arp_rate", set_arp_rate)
    dispatcher.map("/rhythm/density", set_density)
    # Layer toggles would be used by downstream synth; included for completeness
    dispatcher.map("/layer/pad", lambda addr, v: None)
    dispatcher.map("/layer/arp", lambda addr, v: None)
    dispatcher.map("/layer/drums", lambda addr, v: None)

    server = ThreadingOSCUDPServer(("0.0.0.0", args.listen_port), dispatcher)
    print(f"Listening for BCI OSC on {args.listen_port} and sending chords to {args.out_ip}:{args.out_port}")

    # Start scheduler thread
    sched_thread = threading.Thread(target=scheduler_loop, args=(args, bci_state), daemon=True)
    sched_thread.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")


if __name__ == "__main__":
    main() 