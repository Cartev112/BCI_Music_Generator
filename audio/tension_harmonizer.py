from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Tuple, Dict

# ----------------------------------------------
# Data Classes
# ----------------------------------------------

@dataclass(frozen=True)
class Chord:
    """Pitch-class based chord representation (no absolute octave)."""

    root: int  # 0–11 semitone class (C=0)
    quality: str  # 'maj', 'min', '7', 'maj7', 'm7', 'dim', 'aug', 'sus2', 'sus4'
    extensions: Tuple[str, ...] = field(default_factory=tuple)  # e.g. ('9', '11', '#11')
    inversion: int = 0  # 0=root position, 1=first inversion …

    def __post_init__(self):
        if not 0 <= self.root <= 11:
            raise ValueError("root must be 0–11")

    # Convenience
    def __str__(self):
        ext = "".join(self.extensions)
        inv = f"/{self.inversion}" if self.inversion else ""
        return f"{self.root}:{self.quality}{ext}{inv}"


# ----------------------------------------------
# Constants for Tension Calculation
# ----------------------------------------------

QUALITY_WEIGHTS: Dict[str, float] = {
    "maj": 0.0,
    "sus2": 0.0,
    "sus4": 0.0,
    "min": 1.0,
    "7": 2.0,  # dominant 7th
    "maj7": 2.5,
    "m7": 2.5,
    "aug": 3.0,
    "dim": 4.0,
}

DIATONIC_EXTENSIONS = {"9", "11", "13"}
ALTERED_EXTENSIONS = {"b9", "#9", "#11", "b13"}

# Default weights applied to components (can be changed per instance)
DEFAULT_WEIGHTS = (1.5, 1.0, 1.2)  # (w_Q, w_E, w_R)

# ----------------------------------------------
# Helper Functions
# ----------------------------------------------

def circle_of_fifths_distance(a: int, b: int) -> int:
    """Return clockwise steps (0..6) on circle of fifths from a to b."""
    # Circle order: C G D A E B Gb Db Ab Eb Bb F (12 positions)
    # Represent pitch class as mod 12 index along circle-of-fifths (C=0, G=1 ...)
    COF_MAP = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
    inv_map = {pc: i for i, pc in enumerate(COF_MAP)}
    idx_a = inv_map[a]
    idx_b = inv_map[b]
    dist = (idx_b - idx_a) % 12
    return dist if dist <= 6 else 12 - dist  # minimal clockwise distance up to 6


def extension_complexity(ext: Tuple[str, ...]) -> float:
    comp = 0.0
    for e in ext:
        if e in DIATONIC_EXTENSIONS:
            comp += 0.5
        elif e in ALTERED_EXTENSIONS:
            comp += 1.0
    return comp


# ----------------------------------------------
# Library Builder
# ----------------------------------------------

def build_chord_library(
    key_root: int | None = None,
    allowed_qualities: List[str] | None = None,
    allow_altered: bool = True,
) -> List[Chord]:
    """Return a list of candidate chords with optional filtering.

    Parameters
    ----------
    key_root : int | None
        If provided, restrict roots to diatonic scale degrees of the key.
    allowed_qualities : list[str] | None
        If provided, include only chord qualities in this list.
    allow_altered : bool
        If False, exclude altered extensions (b9, #9, #11, b13).
    """
    qualities = [
        "maj",
        "min",
        "7",
        "maj7",
        "m7",
        "dim",
        "aug",
        "sus2",
        "sus4",
    ]

    if allowed_qualities is not None:
        qualities = [q for q in qualities if q in allowed_qualities]

    basic_ext_sets = [(), ("9",), ("9", "11"), ("9", "11", "13")]
    alt_ext_sets = [("#11",), ("b9",), ("#9",)] if allow_altered else []

    chords: List[Chord] = []
    roots = range(12) if key_root is None else [(key_root + i) % 12 for i in range(7)]  # crude diatonic filter

    for root in roots:
        for q in qualities:
            for ext in basic_ext_sets + alt_ext_sets:
                chords.append(Chord(root=root, quality=q, extensions=ext))
    return chords


# ----------------------------------------------
# Tension Calculator with Caching
# ----------------------------------------------

class TensionCalculator:
    def __init__(self, weights: Tuple[float, float, float] = DEFAULT_WEIGHTS):
        self.w_Q, self.w_E, self.w_R = weights

    @lru_cache(maxsize=8192)
    def tension(self, prev_root: int, chord: Chord) -> float:
        Q = QUALITY_WEIGHTS.get(chord.quality, 0.0)
        E = extension_complexity(chord.extensions)
        R = circle_of_fifths_distance(prev_root, chord.root)
        T = self.w_Q * Q + self.w_E * E + self.w_R * R
        return max(0.0, min(10.0, T))

    def set_weights(self, weights: Tuple[float, float, float]):
        """Update weight tuple and clear cache."""
        self.w_Q, self.w_E, self.w_R = weights
        self.tension.cache_clear()


# ----------------------------------------------
# Chord Note Utility
# ----------------------------------------------

NOTE_SEMITONES_TRIAD = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
}

NOTE_SEMITONES_SEVENTH = {
    "7": [0, 4, 7, 10],
    "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10],
}

EXT_SEMITONES = {
    "9": 14,  # 2 an octave up
    "11": 17, # 5 an octave up
    "13": 21, # 9 an octave up
    "b9": 13,
    "#9": 15,
    "#11": 18,
    "b13": 20,
}

def chord_to_pitches(chord: "Chord", octave: int = 4) -> List[int]:
    """Return list of MIDI note numbers (without inversion handling)."""
    base = chord.root + 12 * octave
    if chord.quality in NOTE_SEMITONES_SEVENTH:
        semis = NOTE_SEMITONES_SEVENTH[chord.quality]
    else:
        semis = NOTE_SEMITONES_TRIAD.get(chord.quality, [0, 4, 7])

    notes = [base + s for s in semis]

    # Add extensions
    for ext in chord.extensions:
        if ext in EXT_SEMITONES:
            notes.append(base + EXT_SEMITONES[ext])

    # Apply inversion by moving lowest n notes up an octave
    for i in range(chord.inversion):
        notes[i] += 12
    return sorted(notes)

def voice_leading_cost(c1: "Chord", c2: "Chord") -> float:
    """Heuristic mean absolute semitone distance between closest notes of two chords."""
    p1 = chord_to_pitches(c1)
    p2 = chord_to_pitches(c2)

    # simple greedy matching: for each note in smaller set, find nearest in other set
    if len(p1) > len(p2):
        p1, p2 = p2, p1

    cost_sum = 0.0
    for n in p1:
        closest = min(p2, key=lambda x: abs(x - n))
        cost_sum += abs(closest - n)
    return cost_sum / len(p1)


# ----------------------------------------------
# Harmonizer Engine
# ----------------------------------------------

class TensionHarmonizer:
    def __init__(
        self,
        key: str | None = None,
        weights: Tuple[float, float, float] = DEFAULT_WEIGHTS,
        top_k: int = 4,
    ):
        self.key_root = None if key is None else KEY_TO_PC.get(key.upper(), 0)
        self.library = build_chord_library(self.key_root)
        self.calc = TensionCalculator(weights)
        self.top_k = top_k

        # Preset can be applied later via apply_preset()

    def apply_preset(self, name: str):
        """Apply a reharmonisation preset and rebuild internal structures."""
        if name not in PRESETS:
            raise ValueError(f"Preset '{name}' not found")

        cfg = PRESETS[name]
        # Update weights
        self.calc.set_weights(cfg["weights"])

        # Rebuild chord library with filters
        key_root = self.key_root if cfg.get("key_filter", True) else None
        allowed_qualities = cfg.get("allowed_qualities")
        allow_altered = cfg.get("allow_altered", True)
        self.library = build_chord_library(
            key_root=key_root,
            allowed_qualities=allowed_qualities,
            allow_altered=allow_altered,
        )

    def next_chord(self, prev: Chord, prob_img: float) -> Chord:
        target_T = prob_img * 10.0
        scored = []
        for c in self.library:
            T = self.calc.tension(prev.root, c)
            delta = abs(T - target_T)
            voice_cost = voice_leading_cost(prev, c)
            scored.append((delta, voice_cost, c))

        scored.sort(key=lambda t: (t[0], t[1]))
        candidates = scored[: self.top_k]
        # Weighted random favouring lowest delta
        weights = [1.0 / (1.0 + d[0]) for d in candidates]
        chosen = random.choices([d[2] for d in candidates], weights=weights, k=1)[0]
        return chosen


# ----------------------------------------------
# Utility: note name to pitch class map
# ----------------------------------------------
KEY_TO_PC = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}


# ----------------------------------------------
# Demo when run standalone
# ----------------------------------------------

if __name__ == "__main__":
    import itertools
    import time

    random.seed(42)

    harmonizer = TensionHarmonizer(key="C")
    current = Chord(root=0, quality="maj7")

    print("Starting chord:", current)
    for step in itertools.count():
        prob = abs(math.sin(step * 0.2))  # fake imagery confidence oscillating
        next_c = harmonizer.next_chord(current, prob)
        print(f"prob={prob:.2f} → {next_c} (T={harmonizer.calc.tension(current.root, next_c):.2f})")
        current = next_c
        if step >= 20:
            break
        time.sleep(0.1)

# ----------------------------------------------
# Preset support
# ----------------------------------------------

from presets import PRESETS  # noqa: E402  (import after top definitions) 