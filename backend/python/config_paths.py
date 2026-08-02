from __future__ import annotations

from pathlib import Path


class ProjectPaths:
    def __init__(self, repo_root: str | None = None) -> None:
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[2]).resolve()
        self.backend_dir = self.repo_root / "backend"
        self.python_dir = self.backend_dir / "python"
        self.cpp_dir = self.backend_dir / "cpp"
        self.midi_output_dir = self.repo_root / "MIDI_files"
        self.sheet_output_dir = self.repo_root / "sheet_music"
        self.test_output_dir = self.repo_root / "test_txt_to_excel"
        self.audio_input_dir = self.repo_root / "audio_files"

        for directory in [self.midi_output_dir, self.sheet_output_dir, self.test_output_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def cpp_project_dir(self, algo: str) -> Path:
        mapping = {
            "viterbi": self.cpp_dir / "viterbi_fingering_optimization",
            "pso": self.cpp_dir / "pso_fingering_optimization",
            "main": self.cpp_dir / "main_fingering_optimization",
            "main_plus_viterbi": self.cpp_dir / "main_plus_viterbi_fingering_optimization",
        }
        return mapping.get(algo, self.cpp_dir / f"{algo}_fingering_optimization")

    def cpp_executable(self, algo: str) -> Path:
        return self.cpp_project_dir(algo) / "main.exe"

    def notes_input_path(self, algo: str) -> Path:
        return self.cpp_project_dir(algo) / "notes.txt"

    def output_path(self, file_name: str, *, kind: str) -> Path:
        if kind == "midi":
            return self.midi_output_dir / file_name
        if kind == "sheet":
            return self.sheet_output_dir / file_name
        if kind == "test":
            return self.test_output_dir / file_name
        raise ValueError(f"Unsupported output kind: {kind}")
