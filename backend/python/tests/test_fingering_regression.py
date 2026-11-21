# Ujjrend regressziós teszt: lefuttatja a C++ optimalizálók benchmarkját, és ellenőrzi, hogy a 421 hangos
# benchmarkon pontosan ugyanannyi kedvenc és elfogadható lefogást adnak, mint eddig.
# A benchmark a benchmark_results mappába ír, ezért a teszt a mappa tartalmát a végén visszaállítja
# (a PSO véletlenszerű, különben minden tesztfutás után módosított fájlok maradnának).
# Ha egy eljárás szándékosan változik, az EXPECTED értékeit is frissíteni kell.
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_paths import ProjectPaths
from cpp_optimizer import CppOptimizer

TOTAL_NOTES = 421

# eljárás: (kedvenc lefogás, elfogadható lefogás) a 421 hangból
EXPECTED = {
    "main": (378, 408),
    "main_plus_viterbi": (280, 326),
    "viterbi": (228, 290),
}

PATHS = ProjectPaths()
RESULTS_DIR = PATHS.benchmark_results_dir
NOTE_ACCURACY_RE = re.compile(r"Hang-alapu \(Sulyozott\) pontossag:\s*[\d.]+% \((\d+)/(\d+)\)")


# a benchmark_results mappa fájljainak mentése a tesztek előtt és visszaállítása utánuk
@pytest.fixture(scope="module", autouse=True)
def keep_benchmark_results():
    saved = {}
    if RESULTS_DIR.is_dir():
        for path in RESULTS_DIR.iterdir():
            if path.is_file():
                saved[path] = path.read_bytes()
    yield
    for path, content in saved.items():
        path.write_bytes(content)


# lefuttatja az eljárás benchmarkját, és a log fájlból visszaadja a hang-alapú találatokat:
# [(kedvenc találat, összes), (elfogadható találat, összes)]
def run_benchmark(algo):
    optimizer = CppOptimizer(algo, PATHS)
    if not optimizer.exists():
        pytest.skip(f"nincs lefordítva: {optimizer.cpp_exe}")

    result = optimizer.run_benchmark()
    assert result.returncode == 0, f"a benchmark hibával állt le:\n{result.stderr}"

    log_path = optimizer.benchmark_log_path()
    counts = []
    for match in NOTE_ACCURACY_RE.finditer(log_path.read_text(encoding="utf-8")):
        counts.append((int(match.group(1)), int(match.group(2))))
    assert len(counts) == 2, f"nem található a kedvenc és az elfogadható pontosság a {log_path} fájlban"
    return counts


@pytest.mark.parametrize("algo", sorted(EXPECTED.keys()))
def test_fingering_benchmark_unchanged(algo):
    preferred, accepted = run_benchmark(algo)
    expected_preferred, expected_accepted = EXPECTED[algo]

    assert preferred == (expected_preferred, TOTAL_NOTES), f"{algo} kedvenc lefogás: várt {expected_preferred}/{TOTAL_NOTES}, kapott {preferred[0]}/{preferred[1]}"
    assert accepted == (expected_accepted, TOTAL_NOTES), f"{algo} elfogadható lefogás: várt {expected_accepted}/{TOTAL_NOTES}, kapott {accepted[0]}/{accepted[1]}"


def test_pso_benchmark_runs():
    # a PSO véletlenszerű, ezért itt csak azt nézzük, hogy lefut és mind a 421 hangot kiértékeli
    preferred, accepted = run_benchmark("pso")
    assert preferred[1] == TOTAL_NOTES
    assert accepted[1] == TOTAL_NOTES
