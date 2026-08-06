from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectConfig:
    sample_rate: int = 44100
    stft_nfft: int = 4096
    stft_hop_length: int = 512
    gate_min_gap: float = 0.05
    bpm_default: int = 120
    quantize_resolution: float = 0.25
    lilypond_path: str = r"D:\lilypond-2.24.4\bin\lilypond.exe"
    tab_staff_indent_mm: int = 0
    default_time_signature: str = "4/4"
    default_algo: str = "viterbi"
    supported_algorithms: tuple[str, ...] = ("viterbi", "pso", "main")
