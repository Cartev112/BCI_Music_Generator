import time

import pytest

from tension_harmonizer import (
    Chord,
    TensionCalculator,
    TensionHarmonizer,
)


def test_quality_ranking():
    """Ensure tension ordering for chord qualities follows expected hierarchy."""

    prev_root = 0
    calc = TensionCalculator()

    maj = Chord(root=0, quality="maj")
    minor = Chord(root=0, quality="min")
    dom7 = Chord(root=0, quality="7")
    dim = Chord(root=0, quality="dim")

    t_maj = calc.tension(prev_root, maj)
    t_min = calc.tension(prev_root, minor)
    t_dom7 = calc.tension(prev_root, dom7)
    t_dim = calc.tension(prev_root, dim)

    assert t_maj < t_min < t_dom7 < t_dim


def test_extension_complexity():
    prev_root = 0
    calc = TensionCalculator()

    triad = Chord(root=0, quality="maj", extensions=())
    add9 = Chord(root=0, quality="maj", extensions=("9",))
    alt9 = Chord(root=0, quality="maj", extensions=("b9",))

    assert calc.tension(prev_root, triad) < calc.tension(prev_root, add9) < calc.tension(prev_root, alt9)


def test_harmonizer_speed():
    harmonizer = TensionHarmonizer()
    prev = Chord(root=0, quality="maj")

    start = time.perf_counter()
    for _ in range(1000):
        prev = harmonizer.next_chord(prev, 0.5)
    elapsed = time.perf_counter() - start

    avg_ms = (elapsed / 1000) * 1000
    print(f"Average selection time: {avg_ms:.3f} ms")
    assert avg_ms < 0.5, "Selection too slow (>0.5 ms)" 