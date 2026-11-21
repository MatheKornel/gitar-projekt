# A C++ optimalizálók hívásának (cpp_optimizer.py) tesztjei: a kimenet feldolgozása, a bemeneti fájl formátuma
# és egy valódi futtatás a saját eljárással.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cpp_optimizer import CppOptimizer, OptimizationResult
from note_event import NoteEvent

STANDARD_E = [40, 45, 50, 55, 59, 64]


def test_result_parses_positions_and_time():
    stdout = "Sikeres fajlbetoltes!\nE4\t-\tHur: e\tBund: 0\nB3\t-\tHur: B\tBund: 0\nG2\t-\tHur: E\tBund: 3\n"
    stderr = "Optimalizalas ideje: 0.125 ms\n"
    result = OptimizationResult(0, stdout, stderr, 12.0)
    assert result.positions == [(1, 0), (2, 0), (6, 3)]  # a H húr betűjele B, sorszáma 2
    assert result.optimization_ms == pytest.approx(0.125)
    assert result.other_stderr() == ""


def test_result_keeps_other_stderr_lines():
    result = OptimizationResult(0, "", "Nincs ilyen MIDI hang: 99\nOptimalizalas ideje: 1.5 ms\n", 5.0)
    assert result.optimization_ms == pytest.approx(1.5)
    assert result.other_stderr() == "Nincs ilyen MIDI hang: 99"


def test_result_without_time():
    result = OptimizationResult(1, "", "Hiba", 5.0)
    assert result.optimization_ms is None
    assert result.positions == []


def test_write_input_format(tmp_path):
    path = tmp_path / "notes.txt"
    CppOptimizer.write_input(STANDARD_E, [(64, 0.5, 0.25, "E4"), (45, 1.0, 0.5, "A2")], path)
    assert path.read_text(encoding="utf-8") == "40 45 50 55 59 64\n2\n64 0.5000 0.2500 E4\n45 1.0000 0.5000 A2\n"


def test_notes_from_events_replaces_sharp_sign():
    note = NoteEvent(1.0, 1.5, 466.16)  # A#4
    assert CppOptimizer.notes_from_events([note]) == [(70, 1.0, 0.5, "A#4")]


def test_optimize_runs_main_algorithm(tmp_path):
    optimizer = CppOptimizer("main")
    if not optimizer.exists():
        pytest.skip(f"nincs lefordítva: {optimizer.cpp_exe}")

    # három hang: minden hanghoz kell egy lefogás, az E2 csak az üres vastag E húron szólaltatható meg
    notes = [(40, 0.0, 0.5, "E2"), (55, 0.5, 0.5, "G3"), (57, 1.0, 0.5, "A3")]
    result = optimizer.optimize(STANDARD_E, notes, input_path=tmp_path / "notes.txt")
    assert result.returncode == 0
    assert len(result.positions) == 3
    assert result.positions[0] == (6, 0)
    assert result.optimization_ms is not None
