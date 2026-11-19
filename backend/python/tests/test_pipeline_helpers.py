import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config_parameters
from config_paths import ProjectPaths
from data_to_txt_converter import DataToTxtConverter
from quantizing import Quantizing
from note_event import NoteEvent


def test_project_paths_defaults():
    paths = ProjectPaths()
    assert (paths.repo_root / "backend").is_dir()
    assert paths.backend_dir.name == "backend"
    assert paths.python_dir.name == "python"


def test_project_paths_output_dirs_exist():
    paths = ProjectPaths()
    assert os.path.isdir(paths.midi_output_dir)
    assert os.path.isdir(paths.sheet_output_dir)


def test_cpp_project_dir_uses_expected_folder_names():
    paths = ProjectPaths()
    assert paths.cpp_project_dir("viterbi").name == "viterbi_fingering_optimization"
    assert paths.cpp_project_dir("pso").name == "pso_fingering_optimization"


def test_cpp_executable_name_matches_platform():
    paths = ProjectPaths()
    expected = "main.exe" if os.name == "nt" else "main"
    assert paths.cpp_executable("main").name == expected


def test_data_to_txt_converter_accepts_paths():
    paths = ProjectPaths()
    converter = DataToTxtConverter([], paths=paths)
    assert converter.paths is paths


def _fake_lilypond(root, scm_time, go_time):
    lily = root / "lilypond"
    (lily / "bin").mkdir(parents=True)
    (lily / "bin" / "lilypond.exe").write_text("")
    scm = lily / "share" / "guile" / "eval.scm"
    go = lily / "lib" / "guile" / "ccache" / "eval.go"
    for path, mtime in ((scm, scm_time), (go, go_time)):
        path.parent.mkdir(parents=True)
        path.write_text("")
        os.utime(path, (mtime, mtime))
    return lily / "bin" / "lilypond.exe", scm, go


def test_refresh_bundled_lilypond_cache_makes_go_newer(tmp_path, monkeypatch):
    # Windows Intézős kicsomagolás után a .scm újabb, mint a .go
    exe, scm, go = _fake_lilypond(tmp_path, scm_time=2_000_000, go_time=1_000_000)
    monkeypatch.setattr(config_parameters, "app_root", lambda: tmp_path)
    config_parameters.refresh_bundled_lilypond_cache(exe)
    assert go.stat().st_mtime > scm.stat().st_mtime


def test_refresh_bundled_lilypond_cache_ignores_installed_lilypond(tmp_path, monkeypatch):
    # a gépre telepített (nem a program mellé csomagolt) LilyPondhoz nem nyúlunk
    exe, scm, go = _fake_lilypond(tmp_path / "installed", scm_time=2_000_000, go_time=1_000_000)
    monkeypatch.setattr(config_parameters, "app_root", lambda: tmp_path / "app")
    config_parameters.refresh_bundled_lilypond_cache(exe)
    assert go.stat().st_mtime == 1_000_000


def test_quantizing_keeps_minimum_duration():
    note = NoteEvent(0.2, 0.2, 440.0)
    quantizer = Quantizing([note], grid_resolution=0.25)
    onset, offset = quantizer.quantize(note, 0, 1.0)
    assert offset >= onset + 0.25
