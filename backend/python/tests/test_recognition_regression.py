# Hangfelismerés regressziós teszt: a benchmark felvételein a felismert hangoknak (onset, offset, MIDI)
# pontosan egyezniük kell a tests/data/recognition_golden.json fájlban eltárolt eredménnyel.
# Ha a hangfelismerés szándékosan változik, a golden fájlt az update_recognition_golden.py szkripttel kell frissíteni.
import contextlib
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recognition_regression import GOLDEN_PATH, audio_path, case_names, compare, load_golden, run_case

GOLDEN = load_golden() if GOLDEN_PATH.is_file() else {}


@pytest.mark.parametrize("case_name", case_names())
def test_recognition_matches_golden(case_name):
    if case_name not in GOLDEN:
        pytest.skip("nincs golden érték (update_recognition_golden.py)")
    if audio_path(case_name) is None:
        pytest.skip("a hangfájl nem található (IDMT esetén: IDMT_DATASET_DIR vagy idmt_path.txt)")

    with contextlib.redirect_stdout(io.StringIO()):
        actual = run_case(case_name)

    differences = compare(GOLDEN[case_name], actual)
    assert not differences, f"{case_name} eltér a golden eredménytől:\n  " + "\n  ".join(differences)
