# A hangfelismerés regressziós tesztjének közös része: a tesztesetek, a futtatás és az összehasonlítás.
# A teszt (test_recognition_regression.py) és a golden fájl frissítése (update_recognition_golden.py) is ezt használja.
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_paths import ProjectPaths
from guitar_note_freqs import GuitarNoteFreqs
from recognition_pipeline import load_audio, recognize

PATHS = ProjectPaths()
GOLDEN_PATH = Path(__file__).resolve().parent / "data" / "recognition_golden.json"
IDMT_PATH_FILE = PATHS.repo_root / "idmt_path.txt"
TIME_EPS = 0.001      # a golden fájllal való összevetésnél ennyi eltérés megengedett (kerekítés)

# a két IDMT lick nincs a repóban, csak akkor futnak, ha az adathalmaz megvan a gépen
IDMT_CASES = ["AR_Lick1_FN", "AR_Lick3_FN"]


# az IDMT-SMT-Guitar V2 adathalmaz helye: IDMT_DATASET_DIR környezeti változó, vagy a repó gyökerében az idmt_path.txt
def idmt_dataset_dir():
    path = os.environ.get("IDMT_DATASET_DIR")
    if not path and IDMT_PATH_FILE.is_file():
        for line in IDMT_PATH_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip().strip('"')
            if line and not line.startswith("#"):
                path = line
                break
    if path and Path(path).is_dir():
        return Path(path)
    return None


# a teszteset hangfájlja, vagy None, ha nem található
def audio_path(case_name):
    if case_name in IDMT_CASES:
        dataset_dir = idmt_dataset_dir()
        if dataset_dir is None:
            return None
        path = dataset_dir / "dataset2" / "audio" / f"{case_name}.wav"
    else:
        path = PATHS.audio_input_dir / f"{case_name}.wav"
    if path.is_file():
        return path
    return None


# az összes teszteset: minden benchmark fájl, aminek van hangfájlja (vagy IDMT lick)
def case_names():
    names = []
    for file_name in sorted(os.listdir(PATHS.repo_root / "benchmarks")):
        if file_name.endswith("_fing-opt_test.txt"):
            names.append(file_name.replace("_fing-opt_test.txt", ""))
    return names


# a benchmark fájlból: hangolás neve és a várt hangok MIDI sorozata
def load_ground_truth(case_name):
    open_strings = list(GuitarNoteFreqs.STANDARD_TUNING_MIDI)
    expected = []
    file_path = PATHS.repo_root / "benchmarks" / f"{case_name}_fing-opt_test.txt"
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# tuning:"):
                open_strings = [int(v) for v in line[len("# tuning:"):].split()]
                continue
            if not line or line.startswith("#") or line.startswith("MIDI"):
                continue
            parts = line.split()
            expected.append(int(parts[0]))

    # a hangolás neve abból, hogy hány félhanggal van lejjebb a standard E-nél
    steps = GuitarNoteFreqs.STANDARD_TUNING_MIDI[0] - open_strings[0]
    tuning = "E"
    for name, tuning_steps in GuitarNoteFreqs.TUNING_STEPS.items():
        if tuning_steps == steps:
            tuning = name
    return tuning, expected


# a felismert és a várt hangmagasság-sorozat párosítása (leghosszabb közös részsorozat)
# a benchmark fájlok onsetjei többnyire a tabulatúra ideális időzítéséből jönnek, nem a felvételből,
# ezért itt csak a hangok sorrendje és magassága számít
# TP: párosított hang, FP: felismert, de nem párosított, FN: várt, de nem párosított
def score(detected_midis, expected_midis):
    rows = len(detected_midis) + 1
    cols = len(expected_midis) + 1
    lcs = [[0] * cols for _ in range(rows)]
    for i in range(1, rows):
        for j in range(1, cols):
            if detected_midis[i - 1] == expected_midis[j - 1]:
                lcs[i][j] = lcs[i - 1][j - 1] + 1
            else:
                lcs[i][j] = max(lcs[i - 1][j], lcs[i][j - 1])
    tp = lcs[rows - 1][cols - 1]
    return {"tp": tp, "fp": len(detected_midis) - tp, "fn": len(expected_midis) - tp}


# egy teszteset futtatása: a felismert hangok és a pontosság a benchmark hanglistájához mérve
def run_case(case_name):
    tuning, expected = load_ground_truth(case_name)
    audio, fs = load_audio(audio_path(case_name))
    _, notes, bpm = recognize(audio, fs, tuning)

    result_notes = []
    detected = []
    for n in notes:
        result_notes.append([round(float(n.onset), 4), round(float(n.offset), 4), int(n.midi_note)])
        detected.append(int(n.midi_note))

    result = {"tuning": tuning, "bpm": int(bpm), "notes": result_notes}
    result.update(score(detected, expected))
    return result


def load_golden():
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# mentés olvasható formában: tesztesetenként egy blokk, benne hangonként egy sor [onset, offset, MIDI]
def save_golden(golden):
    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["{"]
    names = sorted(golden.keys())
    for case_idx in range(len(names)):
        name = names[case_idx]
        case = golden[name]
        lines.append(f'  "{name}": {{')
        lines.append(f'    "tuning": {json.dumps(case["tuning"], ensure_ascii=False)}, "bpm": {case["bpm"]}, '
                     f'"tp": {case["tp"]}, "fp": {case["fp"]}, "fn": {case["fn"]},')
        lines.append('    "notes": [')
        for note_idx in range(len(case["notes"])):
            separator = "," if note_idx < len(case["notes"]) - 1 else ""
            lines.append(f"      {json.dumps(case['notes'][note_idx])}{separator}")
        lines.append("    ]")
        lines.append("  }," if case_idx < len(names) - 1 else "  }")
    lines.append("}")
    with open(GOLDEN_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# két futás összevetése; visszaadja az eltérések szöveges listáját (üres lista = egyezik)
def compare(expected, actual):
    differences = []
    for key in ("tuning", "bpm", "tp", "fp", "fn"):
        if expected[key] != actual[key]:
            differences.append(f"{key}: várt {expected[key]}, kapott {actual[key]}")

    exp_notes = expected["notes"]
    act_notes = actual["notes"]
    if len(exp_notes) != len(act_notes):
        differences.append(f"hangok száma: várt {len(exp_notes)}, kapott {len(act_notes)}")

    for i in range(min(len(exp_notes), len(act_notes))):
        e = exp_notes[i]
        a = act_notes[i]
        if abs(e[0] - a[0]) > TIME_EPS or abs(e[1] - a[1]) > TIME_EPS or e[2] != a[2]:
            differences.append(f"{i + 1}. hang: várt (onset {e[0]}, offset {e[1]}, MIDI {e[2]}), kapott (onset {a[0]}, offset {a[1]}, MIDI {a[2]})")
    return differences
