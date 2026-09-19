from __future__ import annotations

import glob
import os
import platform
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path


# A LilyPond keresési sorrendje (lásd _resolve_lilypond_path):
#   1. LILYPOND_PATH környezeti változó
#   2. a projektben elhelyezett "lilypond_path.txt" (gépenként eltérhet,
#      érdemes .gitignore-ba tenni)
#   3. PATH
#   4. music21 saját, felhasználónként eltárolt beállítása
#   5. tipikus telepítési könyvtárak (Windows / macOS / Linux)
_LOCAL_PATH_FILE = "lilypond_path.txt"


def _exe_name() -> str:
    return "lilypond.exe" if os.name == "nt" else "lilypond"


def _is_usable(path) -> bool:
    if not path:
        return False
    p = Path(path)
    if not p.is_file():
        return False
    return os.access(p, os.F_OK if os.name == "nt" else os.X_OK)


def _from_env():
    return os.environ.get("LILYPOND_PATH")


def _from_local_file():
    """A lilypond_path.txt első nem üres, nem kommentezett sora."""
    here = Path(__file__).resolve()
    candidates = [here.parent / _LOCAL_PATH_FILE]
    # a projekt gyökere is szóba jöhet (backend/python/... -> gyökér)
    for up in (1, 2, 3):
        if len(here.parents) > up:
            candidates.append(here.parents[up] / _LOCAL_PATH_FILE)

    for candidate in candidates:
        try:
            if candidate.is_file():
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip().strip('"')
                    if line and not line.startswith("#"):
                        return line
        except OSError:
            continue
    return None


def _from_path():
    return shutil.which("lilypond") or shutil.which("lilypond.exe")


def _from_music21():
    """A music21 felhasználónként elmenti a beállított lilypondPath-t."""
    try:
        from music21 import environment

        return environment.Environment()["lilypondPath"]
    except Exception:
        return None


def _version_key(path: str):
    """Verziószám az útvonalból, hogy a legújabb telepítést válasszuk."""
    numbers = re.findall(r"(\d+)\.(\d+)(?:\.(\d+))?", path)
    if not numbers:
        return (0, 0, 0)
    major, minor, patch = numbers[-1]
    return (int(major), int(minor), int(patch or 0))


def _from_common_locations():
    exe = _exe_name()
    system = platform.system()
    patterns = []

    if system == "Windows":
        roots = []
        for letter in "CDEFG":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                roots += [
                    os.path.join(drive, "Program Files"),
                    os.path.join(drive, "Program Files (x86)"),
                    drive,
                ]
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            roots.append(os.path.join(local_appdata, "Programs"))

        for root in roots:
            patterns += [
                os.path.join(root, "lilypond*", "bin", exe),
                os.path.join(root, "lilypond*", "usr", "bin", exe),
            ]
    elif system == "Darwin":
        patterns += [
            f"/Applications/LilyPond.app/Contents/Resources/bin/{exe}",
            f"/Applications/lilypond*/bin/{exe}",
            f"/opt/homebrew/bin/{exe}",
            f"/usr/local/bin/{exe}",
            os.path.expanduser(f"~/Applications/LilyPond.app/Contents/Resources/bin/{exe}"),
        ]
    else:  # Linux és egyéb
        patterns += [
            f"/usr/bin/{exe}",
            f"/usr/local/bin/{exe}",
            f"/snap/bin/{exe}",
            f"/opt/lilypond*/bin/{exe}",
            os.path.expanduser(f"~/.local/bin/{exe}"),
            os.path.expanduser(f"~/lilypond*/bin/{exe}"),
        ]

    found = []
    for pattern in patterns:
        found += [p for p in glob.glob(pattern) if _is_usable(p)]

    if not found:
        return None
    return max(found, key=_version_key)


def _resolve_lilypond_path() -> str:
    for source in (_from_env, _from_local_file, _from_path, _from_music21, _from_common_locations):
        candidate = source()
        if _is_usable(candidate):
            return str(candidate)
    # Nem találtuk meg: a puszta nevet adjuk vissza, így a hibaüzenet értelmes
    # marad, és ha közben felkerül a PATH-ra, működni fog.
    return _exe_name()


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