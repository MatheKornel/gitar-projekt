from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field


_LILYPOND_FALLBACK = r"C:\Users\z005aumf\Documents\Máthé Kornél\lilypond-2.26.0\bin\lilypond.exe"


def _resolve_lilypond_path() -> str:
    env_path = os.environ.get("LILYPOND_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    path_exe = shutil.which("lilypond")
    if path_exe:
        return path_exe

    return _LILYPOND_FALLBACK


@dataclass
class ProjectConfig:
    sample_rate: int = 44100
    stft_nfft: int = 4096
    stft_hop_length: int = 512
    gate_min_gap: float = 0.05
    bpm_default: int = 120
    quantize_resolution: float = 0.25
    lilypond_path: str = field(default_factory=_resolve_lilypond_path)
    tab_staff_indent_mm: int = 0
    default_time_signature: str = "4/4"
    default_algo: str = "viterbi"
    supported_algorithms: tuple[str, ...] = ("viterbi", "pso", "main")
