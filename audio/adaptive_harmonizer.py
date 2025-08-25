from collections import deque
from typing import Tuple

from tension_harmonizer import (
    TensionHarmonizer,
    TensionCalculator,
    DEFAULT_WEIGHTS,
    Chord,
)


class AdaptiveTensionHarmonizer(TensionHarmonizer):
    """Harmonizer that slowly adjusts weighting factors to minimize tension error."""

    def __init__(
        self,
        key: str | None = None,
        weights: Tuple[float, float, float] = DEFAULT_WEIGHTS,
        top_k: int = 4,
        lr: float = 0.05,
        history_len: int = 32,
    ):
        super().__init__(key=key, weights=weights, top_k=top_k)
        self.lr = lr
        self.error_hist = deque(maxlen=history_len)

    def _update_weights(self, error: float):
        # Simple proportional update: increase w_Q & w_E if error sign positive, else decrease
        w_Q, w_E, w_R = self.calc.w_Q, self.calc.w_E, self.calc.w_R
        delta = self.lr * error
        # Distribute delta proportionally
        w_E += 0.5 * delta
        w_R += 0.3 * delta
        w_Q += 0.2 * delta
        # Clamp non-negative
        w_Q = max(0.1, w_Q)
        w_E = max(0.1, w_E)
        w_R = max(0.1, w_R)
        self.calc.set_weights((w_Q, w_E, w_R))

    def next_chord(self, prev: Chord, prob_img: float) -> Chord:
        chord = super().next_chord(prev, prob_img)
        # Compute error between achieved tension and target
        target_T = prob_img * 10.0
        achieved_T = self.calc.tension(prev.root, chord)
        error = target_T - achieved_T
        self.error_hist.append(error)
        # Update weights every few samples to avoid oscillation
        if len(self.error_hist) == self.error_hist.maxlen:
            mean_err = sum(self.error_hist) / len(self.error_hist)
            self._update_weights(mean_err)
            self.error_hist.clear()
        return chord 