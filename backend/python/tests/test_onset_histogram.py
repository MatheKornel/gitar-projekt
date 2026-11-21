# A tempóbecslés (onset_histogram.py) tesztjei egyszerű, szabályos ritmusokon.
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from onset_histogram import DEFAULT_BPM, estimate_bpm, inter_onset_intervals


def regular_onsets(beat_length, count=40):
    return np.arange(count) * beat_length + 1.0


def test_too_few_onsets_gives_default_bpm():
    assert estimate_bpm([]) == DEFAULT_BPM
    assert estimate_bpm([0.5, 1.0, 1.5]) == DEFAULT_BPM


def test_quarter_notes_at_120_bpm():
    assert estimate_bpm(regular_onsets(0.5)) == 120


def test_fast_notes_are_folded_into_fast_range():
    # 0.15 s-os hangok: 400 BPM lenne, a gyors tartományba (100-220) felezve 200
    assert estimate_bpm(regular_onsets(0.15)) == 200


def test_slow_notes_are_doubled_into_normal_range():
    # 0.9 s-os időköz: kb. 67 BPM, ez már a normál tartományban (60-160) van
    assert 60 <= estimate_bpm(regular_onsets(0.9)) <= 160


def test_intervals_outside_limits_are_dropped():
    # 0.01 s (zaj) és 2 s (szünet) kimarad, csak a 0.5 s-os időköz marad
    iois = inter_onset_intervals([0.0, 0.01, 0.51, 2.51])
    assert np.allclose(iois, [0.5])
