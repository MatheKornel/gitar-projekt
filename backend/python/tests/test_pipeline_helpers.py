import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def test_data_to_txt_converter_accepts_paths():
    paths = ProjectPaths()
    converter = DataToTxtConverter([], paths=paths)
    assert converter.paths is paths


def test_quantizing_keeps_minimum_duration():
    note = NoteEvent(0.2, 0.2, 440.0)
    quantizer = Quantizing([note], grid_resolution=0.25)
    onset, offset = quantizer.quantize(note, 0, 1.0)
    assert offset >= onset + 0.25
