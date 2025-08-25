# Chord Tension Algorithm – Detailed Design

## 0. Context
This algorithm sits inside the *Music Controller* layer and is responsible for generating an endless chord sequence whose **tension** follows the real-time mental-imagery confidence (`prob_img`, range 0–1) coming from the BCI classifier.  
A *tension constant* \(T\_{chord} \in [0,10]\) is pre-computed for every chord candidate, and during playback the module continually selects the next chord whose tension best matches the *target* tension (derived from `prob_img`).

---

## 1. Data Representation
1. **Pitch Model** – 12-TET, MIDI note numbers.  
2. **Chord Object**  
```python
@dataclass(frozen=True)
class Chord:
    root: int          # 0–11 semitone class
    quality: str       # e.g. 'maj', 'min', 'dim', 'aug', '7', 'm7', 'maj7', …
    extensions: tuple[int]  # extra scale-degrees as semitone offsets (9, 11, 13, #11, b9, …)
    inversion: int = 0 # bass position (0 = root)
```
3. **Chord Library** – finite set (≈ 500) within a key or all 12 roots.  
   • Pre-generated on module load and cached.

---

## 2. Computing the Tension Constant \(T\_{chord}\)
The constant is a weighted sum of three components:

| Component | Symbol | Range | Rationale |
|-----------|--------|-------|-----------|
| Quality weight | \(Q\) | 0–4 | dim/aug > min > maj |
| Extension complexity | \(E\) | 0–3 | more altered/added notes ⇒ higher tension |
| Interval drifts | \(R\) | 0–3 | bigger leap (tritone) from previous root ⇒ more tension |

Formula (linear to keep CPU low):  
\[ T\_{chord} = w\_Q Q + w\_E E + w\_R R \quad\text{(clamped 0–10)} \]
Default weights \(w\_Q = 1.5,\, w\_E = 1.0,\, w\_R = 1.2;\) tweak in config.

Component Details
1. **Q – Chord Quality Table**
```
maj / sus2 / sus4   → 0
min                → 1
7 (dominant)       → 2
maj7 / m7          → 2.5
aug                → 3
º (diminished)     → 4
```
2. **E – Extensions** (sum)
```
  +0.5  for each diatonic add (9, 11, 13)
  +1.0  for each altered (b9, #9, #11, b13)
```
3. **R – Root Movement**  
Let \(d\) be the *clockwise* circle-of-fifths distance (0..6) between current root and *previous* root.
```
0/1 steps → 0         (smooth)
2/3 steps → 1         (moderate)
4 steps   → 2
5/6 steps → 3         (tritone / far)
```

All values cached per (prev_root, chord) pair for O(1) lookup.

---

## 3. Runtime Algorithm
```python
state = init_chord
while playing:
    target_T  = map_lin(prob_img, 0, 1, 0, 10)
    candidates = chords_by_root[state.root]  # or full library
    scored = [(abs(T[c] - target_T), voice_lead_cost(state, c), c) for c in candidates]
    scored.sort(key=lambda t: (t[0], t[1]))      # tension closeness then smoothness
    next_chord = weighted_random(scored[:K])     # K≈4 avoid determinism
    play(next_chord)
    state = next_chord
```
Voice-leading cost = mean absolute semitone movement per voice (favour minimal motion).

### Efficiency Notes
* `T` is a dict mapping `Chord`→float, computed once.
* Root-indexed buckets avoid full scans.
* Uses cheap linear math; no realtime DSP.

---

## 4. API Outline
```python
class TensionHarmonizer:
    def __init__(self, key='C', weights=(1.5,1.0,1.2)):
        build_library()
    def next_chord(self, prev: Chord, prob_img: float) -> Chord:
        ...
```
Outputs chord as MIDI note list or as OSC bundle `/bci/chord [root, quality, ...]`.

---

## 5. Possible Enhancements
1. **Adaptive Weights** – learn user preference via reinforcement signal.
2. **Temporal Decay** – include moving average of `prob_img` to avoid abrupt jumps.
3. **Mode Support** – switch libraries for different tonal centres when prob_img crosses threshold.
4. **Secondary Metric** – use EEG *engagement* to influence tempo or density.

---

## 6. Development Roadmap
1. **Phase A – Core Library**  
   • Implement `Chord` dataclass + parsing helpers.  
   • Build chord library in current key.  
   • Implement tension calculation + caching.
2. **Phase B – Harmonizer Engine**  
   • Greedy + weighted-random selection.  
   • Voice-leading cost function.
3. **Phase C – Integration**  
   • Wrap into OSC-driven service; respond to `/bci/prob_img`.  
   • Output next chord every N beats via OSC/MIDI.
4. **Phase D – Optimisation & Tests**  
   • Unit tests for tension formula.  
   • Benchmark to stay < 0.5 ms per selection.
5. **Phase E – Enhancements**  
   • Adaptive weights, reharmonisation presets, user feedback loop.

---
*Design v1 – ready for implementation.* 