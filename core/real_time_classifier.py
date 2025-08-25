import argparse
import time
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
import joblib
from pythonosc import udp_client

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, LogLevels
from brainflow.data_filter import DataFilter, FilterTypes
try:
    from data.features import compute_epoch_features
except ImportError:
    from core.features import compute_epoch_features

# ---------------------------
# Frequency bands (Hz) — must match offline training
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 50),
}

# --------------------------------
# Feature extraction helpers
# --------------------------------

def preprocess_window(window: np.ndarray, fs: int):
    """Apply filters and re-reference on a window (channels x samples)."""
    for ch in range(window.shape[0]):
        DataFilter.perform_bandpass(window[ch], fs, 20.0, 38.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        DataFilter.perform_lowpass(window[ch], fs, 40.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        DataFilter.perform_highpass(window[ch], fs, 1.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        DataFilter.perform_notch(window[ch], fs, 60.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
    # Common average reference
    window -= np.mean(window, axis=0, keepdims=True)
    return window

# --------------------------------
# Real-time processing class
# --------------------------------

class RealTimeBCI:
    def __init__(self, args):
        self.args = args
        self.model = joblib.load(args.model_path)

        self.params = BrainFlowInputParams()
        self.params.serial_port = args.serial_port
        self.params.timeout = args.timeout

        self.board = BoardShim(args.board_id, self.params)
        BoardShim.enable_dev_board_logger() if args.verbose else BoardShim.set_log_level(LogLevels.LEVEL_OFF)

        self.sr = BoardShim.get_sampling_rate(args.board_id)
        self.eeg_channels = BoardShim.get_eeg_channels(args.board_id)

        self.window_samples = int(args.window_size * self.sr)
        self.step_samples = int(args.step_size * self.sr)
        self.buffer = deque(maxlen=self.window_samples)

        # Setup OSC if requested
        if args.enable_osc:
            self.osc_client = udp_client.SimpleUDPClient(args.osc_ip, args.osc_port)
            self.send_prob = args.send_prob
        else:
            self.osc_client = None
            self.send_prob = False

        self.pred_history = deque(maxlen=args.smooth_n)

    def start(self):
        print("Preparing session…")
        self.board.prepare_session()
        self.board.start_stream(450000)
        print("Streaming started. Press Ctrl+C to stop.")
        try:
            while True:
                data = self.board.get_board_data()  # returns all new data since last call
                if data.size != 0:
                    # Append eeg channel samples to buffer
                    data_eeg = data[self.eeg_channels, :]
                    for i in range(data_eeg.shape[1]):
                        # For each sample column
                        sample = data_eeg[:, i]
                        self.buffer.append(sample)
                # Process when enough samples accumulated and step threshold met
                if len(self.buffer) == self.window_samples:
                    # buffer holds one array per sample (n_ch,). Convert to (n_ch, window_samples)
                    window = np.asarray(self.buffer)  # (win, n_ch)
                    window = window.T                # (n_ch, win)
                    features = self.process_window(window)
                    pred = int(self.model.predict(features.reshape(1, -1))[0])
                    probs = None
                    if self.send_prob:
                        try:
                            probs = self.model.predict_proba(features.reshape(1, -1))[0]
                        except Exception:
                            probs = None
                    self.pred_history.append(pred)
                    if len(self.pred_history) == self.pred_history.maxlen and all(p == self.pred_history[0] for p in self.pred_history):
                        self.act_on_prediction(pred)
                    if self.osc_client:
                        # status updates for UI LEDs
                        self.osc_client.send_message("/status/board", 1)
                        self.osc_client.send_message("/status/classifier", 1)
                        self.osc_client.send_message("/status/osc", 1)
                        if self.send_prob and probs is not None:
                            self.osc_client.send_message("/bci/prob_img", float(probs[1]))
                    # Remove step samples from buffer to slide window
                    for _ in range(self.step_samples):
                        if self.buffer:
                            self.buffer.popleft()
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("\nStopping…")
        finally:
            self.board.stop_stream()
            self.board.release_session()
            print("Session released. Goodbye!")

    def process_window(self, window: np.ndarray):
        # window shape (n_ch, window_samples)
        window = preprocess_window(window, self.sr)
        feats = compute_epoch_features(window, self.sr)
        return feats

    def act_on_prediction(self, pred):
        label = "IMAGERY" if pred == 1 else "REST"
        print(f"Prediction: {label}")
        if self.osc_client:
            # Send /bci/state 1 or 0
            self.osc_client.send_message("/bci/state", int(pred))


# ---------------------------
# CLI
# ---------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Real-time EEG classification using trained model.")
    parser.add_argument("--serial-port", required=True, help="Serial port of Ganglion board (e.g., COM3)")
    parser.add_argument("--model-path", required=True, type=Path, help="Path to joblib-trained model")
    parser.add_argument("--board-id", type=int, default=BoardIds.GANGLION_BOARD.value)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--window-size", type=float, default=4.0, help="Window length in seconds")
    parser.add_argument("--step-size", type=float, default=1.0, help="Sliding step in seconds")
    parser.add_argument("--smooth-n", type=int, default=3, help="Consecutive identical predictions to confirm")
    parser.add_argument("--enable-osc", action="store_true", help="Send OSC messages on state changes")
    parser.add_argument("--send-prob", action="store_true", help="Also send imagery probability as /bci/prob_img <float>")
    parser.add_argument("--osc-ip", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=9000)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    rtbci = RealTimeBCI(args)
    rtbci.start()


if __name__ == "__main__":
    main() 