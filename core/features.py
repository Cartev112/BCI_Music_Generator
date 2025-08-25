try:
  # Prefer local features if present
  from datatraintest.features import (
      compute_epoch_features,
      compute_channel_features,
      BANDS,
  )  # type: ignore
except Exception:  # pragma: no cover
  # Fallback minimal implementation if datatraintest not available
  from typing import Tuple
  import numpy as np

  BANDS = {
      "delta": (1, 4),
      "theta": (4, 8),
      "alpha": (8, 13),
      "beta": (13, 30),
      "gamma": (30, 50),
  }

  def compute_channel_features(sig: np.ndarray, fs: int) -> np.ndarray:
      return np.array([
          np.mean(sig), np.std(sig), np.ptp(sig),
      ], dtype=float)

  def compute_epoch_features(epoch: np.ndarray, fs: int) -> np.ndarray:
      feats = [compute_channel_features(epoch[ch], fs) for ch in range(epoch.shape[0])]
      return np.concatenate(feats)




