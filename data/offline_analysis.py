import argparse
from pathlib import Path
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations
from features import compute_epoch_features  # NEW

# ---------------------------
# Constants & Helper Settings
# ---------------------------
# Frequency bands (Hz)
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 50),
}

# Marker values (keep in sync with acquisition script)
REST_MARKER = 1.0
IMAGERY_MARKER = 2.0


def load_brainflow_csv(csv_path: Path, board_id: int):
    """Load a BrainFlow CSV file and return EEG data, marker channel, and sampling rate."""
    # Read entire CSV to numpy array (rows=channels, cols=samples)
    data = DataFilter.read_file(csv_path.as_posix(), BoardShim.get_num_rows(board_id))
    data = np.asarray(data)

    fs = BoardShim.get_sampling_rate(board_id)
    eeg_chs = BoardShim.get_eeg_channels(board_id)
    marker_ch = BoardShim.get_marker_channel(board_id)

    eeg_data = data[eeg_chs, :]  # shape (n_channels, n_samples)
    markers = data[marker_ch, :]

    return eeg_data, markers, fs


def preprocess_eeg(eeg: np.ndarray, fs: int):
    """Band-pass (1-40Hz) and notch-filter at power-line frequency."""
    for ch in range(eeg.shape[0]):
        # Band-pass
        DataFilter.perform_bandpass(eeg[ch], fs, 20.0, 38.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        DataFilter.perform_lowpass(eeg[ch], fs, 40.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        DataFilter.perform_highpass(eeg[ch], fs, 1.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)
        # Notch at 60 Hz (change to 50 if required)
        DataFilter.perform_notch(eeg[ch], fs, 60.0, 4, FilterTypes.BESSEL_ZERO_PHASE, 0)

    # Re-reference to common average
    eeg -= np.mean(eeg, axis=0, keepdims=True)
    return eeg


def find_epoch_indices(markers: np.ndarray, fs: int, epoch_len: float = 4.0, offset: float = 2.0):
    """Return list of (start_idx, end_idx, label) tuples for each epoch."""
    idxs = np.where(markers != 0)[0]  # indices where a marker was inserted
    epochs = []
    samples_per_epoch = int(epoch_len * fs)
    offset_samples = int(offset * fs)

    for idx in idxs:
        label_val = markers[idx]
        # Start epoch after offset to avoid cue artefacts
        start = idx + offset_samples
        end = start + samples_per_epoch
        if end <= len(markers):
            label = 0 if label_val == REST_MARKER else 1  # 0=Rest, 1=Imagery
            epochs.append((start, end, label))
    return epochs


def extract_features(eeg: np.ndarray, epochs, fs: int):
    """Return X matrix and y labels leveraging compute_epoch_features from features module."""
    X, y = [], []
    for start, end, label in epochs:
        epoch = eeg[:, start:end]
        X.append(compute_epoch_features(epoch, fs))
        y.append(label)
    return np.vstack(X), np.array(y)


def build_classifier():
    """Return an sklearn Pipeline with StandardScaler and SVM + grid search."""
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC(probability=True)),
    ])

    param_grid = {
        "svc__C": [0.1, 1, 10],
        "svc__gamma": ["scale", 0.01, 0.001],
        "svc__kernel": ["rbf"],
    }
    clf = GridSearchCV(pipe, param_grid, cv=5, n_jobs=-1)
    return clf


def main():
    parser = argparse.ArgumentParser(description="Offline EEG Signal Processing & Model Training")
    parser.add_argument("--input-file", required=True, help="Path to BrainFlow CSV file saved from acquisition script.")
    parser.add_argument("--board-id", type=int, default=BoardIds.GANGLION_BOARD.value, help="Board ID used during recording.")
    parser.add_argument("--model-out", default="svm_model.joblib", help="Filename to save the trained model.")
    args = parser.parse_args()

    csv_path = Path(args.input_file)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    print("Loading data ...")
    eeg, markers, fs = load_brainflow_csv(csv_path, args.board_id)
    print(f"EEG shape: {eeg.shape}, Sampling rate: {fs} Hz")

    print("Pre-processing ...")
    eeg = preprocess_eeg(eeg, fs)

    print("Epoching ...")
    epochs_meta = find_epoch_indices(markers, fs)
    print(f"Total epochs found: {len(epochs_meta)}")

    if not epochs_meta:
        raise RuntimeError("No epochs found. Check marker values and recording duration.")

    print("Extracting features ...")
    X, y = extract_features(eeg, epochs_meta, fs)
    print(f"Feature matrix shape: {X.shape}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = build_classifier()
    print("Training classifier (SVM with grid search) ...")
    clf.fit(X_train, y_train)
    print(f"Best params: {clf.best_params_}")

    print("Evaluating ...")
    y_pred = clf.predict(X_test)
    print("Classification Report:\n", classification_report(y_test, y_pred))
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
    print("Accuracy:", accuracy_score(y_test, y_pred))

    # Save the best estimator
    joblib.dump(clf.best_estimator_, args.model_out)
    print(f"Model saved to {args.model_out}")


if __name__ == "__main__":
    main() 