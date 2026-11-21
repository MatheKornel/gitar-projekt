from __future__ import annotations

from dataclasses import dataclass, field

from lilypond_locator import resolve_lilypond_path


# a kotta generálásának beállításai
@dataclass
class ProjectConfig:
    lilypond_path: str = field(default_factory=resolve_lilypond_path)  # a LilyPond futtatható fájl (lásd lilypond_locator.py)
    default_time_signature: str = "4/4"                                # ütemmutató a kottában
