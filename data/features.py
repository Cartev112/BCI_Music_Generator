import numpy as np
from scipy.signal import welch

# ---------------------------
# Constants
# ---------------------------
BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 50),
}

# --------------------------------
# Feature Functions
# --------------------------------

def _bandpower(sig: np.ndarray, fs: int, band):
    """Return absolute power of `sig` within frequency `band` (low, high)."""
    f, pxx = welch(sig, fs, nperseg=fs * 2)
    idx = np.logical_and(f >= band[0], f <= band[1])
    return np.trapz(pxx[idx], f[idx])


def _hjorth_params(sig: np.ndarray):
    """Return Hjorth Activity, Mobility, Complexity for a signal."""
    first_deriv = np.diff(sig)
    second_deriv = np.diff(first_deriv)
    var_zero = np.var(sig)
    var_d1 = np.var(first_deriv)
    var_d2 = np.var(second_deriv)

    activity = var_zero
    mobility = np.sqrt(var_d1 / var_zero) if var_zero > 0 else 0
    complexity = np.sqrt(var_d2 / var_d1) / mobility if var_d1 > 0 and mobility > 0 else 0
    return activity, mobility, complexity


def compute_channel_features(sig: np.ndarray, fs: int):
    """Compute a set of features for a single-channel signal segment."""
    # Absolute bandpowers
    abs_powers = np.array([_bandpower(sig, fs, band) for band in BANDS.values()])
    total_power = np.sum(abs_powers)

    # Relative bandpowers (band / total)
    rel_powers = abs_powers / total_power if total_power > 0 else np.zeros_like(abs_powers)

    # Bandpower ratios (example: alpha/beta)
    alpha_beta_ratio = abs_powers[2] / abs_powers[3] if abs_powers[3] > 0 else 0

    # Hjorth parameters
    activity, mobility, complexity = _hjorth_params(sig)

    # Concatenate features
    feats = np.concatenate([
        abs_powers,          # 5 values
        rel_powers,          # 5 values
        np.array([alpha_beta_ratio]), # 1
        np.array([activity, mobility, complexity])  # 3
    ])
    return feats


def compute_epoch_features(epoch: np.ndarray, fs: int):
    """Return feature vector for an epoch (channels x samples)."""
    feats = [compute_channel_features(epoch[ch], fs) for ch in range(epoch.shape[0])]
    return np.concatenate(feats) 