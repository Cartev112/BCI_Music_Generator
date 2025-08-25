import random
from typing import List


class Arpeggiator:
    """Stateful arpeggiator that cycles through chord pitches in various patterns."""

    MODES = {"up", "down", "updown", "random", "off"}

    def __init__(self, mode: str = "up", gate: float = 0.9):
        if mode not in self.MODES:
            raise ValueError(f"Invalid arpeggio mode: {mode}")
        self.mode = mode
        self.gate = max(0.05, min(1.0, gate))  # fraction of note length
        self._pitches: List[int] = []
        self._index = 0
        self._direction = 1  # used for updown

    # ----------------------------------
    # Configuration
    # ----------------------------------

    def set_mode(self, mode: str):
        if mode not in self.MODES:
            raise ValueError(mode)
        self.mode = mode
        self.reset()

    def set_chord(self, pitches: List[int]):
        self._pitches = sorted(pitches)
        self.reset()

    def reset(self):
        self._index = 0 if self.mode != "down" else len(self._pitches) - 1
        self._direction = 1

    # ----------------------------------
    # Generation
    # ----------------------------------

    def next_pitch(self):
        if self.mode == "off" or not self._pitches:
            return None

        if self.mode == "random":
            return random.choice(self._pitches)

        pitch = self._pitches[self._index]

        if self.mode == "up":
            self._index = (self._index + 1) % len(self._pitches)
        elif self.mode == "down":
            self._index = (self._index - 1) % len(self._pitches)
        elif self.mode == "updown":
            if self._direction == 1:
                if self._index >= len(self._pitches) - 1:
                    self._direction = -1
                    self._index -= 1
                else:
                    self._index += 1
            else:  # currently descending
                if self._index <= 0:
                    self._direction = 1
                    self._index += 1
                else:
                    self._index -= 1
        return pitch 