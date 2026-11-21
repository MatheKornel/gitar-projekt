import re
import subprocess
import time

from config_paths import ProjectPaths

# a négy ujjrend optimalizáló azonosítója (a C++ mappák neve: <azonosító>_fingering_optimization)
ALGORITHMS = ['main', 'main_plus_viterbi', 'viterbi', 'pso']

# a C++ kimenetében a lefogások: "Hur: <húr betűjele> Bund: <szám>" (a H húr betűjele B)
POSITION_RE = re.compile(r"Hur:\s*([EADGBe])\s*Bund:\s*(\d+)")
# a C++ a standard hibakimenetre írja az optimalizálás idejét: "Optimalizalas ideje: <szám> ms"
OPT_TIME_RE = re.compile(r"Optimalizalas ideje:\s*([0-9.eE+-]+)\s*ms")
# a húr betűjeléből a húr sorszáma (1 = vékony e, 6 = vastag E)
STRING_NUMBERS = {'e': 1, 'B': 2, 'G': 3, 'D': 4, 'A': 5, 'E': 6}


# egy fájlos futtatás eredménye
class OptimizationResult:
    def __init__(self, returncode, stdout, stderr, total_ms):
        self.returncode = returncode  # a C++ program kilépési kódja (0 = sikeres)
        self.stdout = stdout
        self.stderr = stderr
        self.total_ms = total_ms      # a teljes futás ideje a program indításától (ms)

        # hangonként a (húr, bund) pár, a C++ kimenetének sorrendjében
        self.positions = []
        for string_letter, fret in POSITION_RE.findall(stdout):
            self.positions.append((STRING_NUMBERS[string_letter], int(fret)))

        # az optimalizálás saját ideje a C++ mérése szerint (ms), None, ha nincs a kimenetben
        match = OPT_TIME_RE.search(stderr)
        self.optimization_ms = float(match.group(1)) if match else None

    # a standard hibakimenet az időmérés sora nélkül (ami marad, az figyelmeztetés vagy hiba)
    def other_stderr(self):
        return OPT_TIME_RE.sub("", self.stderr).strip()


# A C++ ujjrend optimalizálók hívása: a bemeneti fájl megírása, a program futtatása és a kimenet feldolgozása.
# Ezt használja a GUI, a benchmark és a futásidő mérés is.
class CppOptimizer:
    def __init__(self, algo, paths=None):
        self.algo = algo  # main, main_plus_viterbi, viterbi vagy pso
        self.paths = paths or ProjectPaths()
        self.cpp_exe = self.paths.cpp_executable(algo)

    def exists(self):
        return self.cpp_exe.exists()

    # az alkalmazás bemeneti fájlja (notes.txt a program mappájában)
    def default_input_path(self):
        return self.paths.notes_input_path(self.algo)

    # NoteEvent listából a bemeneti fájl sorai: (MIDI, onset, hossz, hangnév)
    @staticmethod
    def notes_from_events(note_events):
        notes = []
        for note in note_events:
            notes.append((int(note.midi_note), note.onset, note.duration, note.note_name.replace("♯", "#")))
        return notes

    # a bemeneti fájl: első sor a 6 üres húr MIDI hangja, utána a hangok száma, majd soronként egy hang
    @staticmethod
    def write_input(open_strings, notes, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(" ".join(str(m) for m in open_strings) + "\n")
            f.write(f"{len(notes)}\n")
            for midi, onset, duration, name in notes:
                f.write(f"{midi} {onset:.4f} {duration:.4f} {name}\n")

    # egy már megírt bemeneti fájl optimalizálása
    def run_file(self, input_path):
        start = time.perf_counter()
        result = subprocess.run([str(self.cpp_exe), str(input_path)], cwd=str(self.cpp_exe.parent), capture_output=True, text=True)
        total_ms = (time.perf_counter() - start) * 1000.0
        return OptimizationResult(result.returncode, result.stdout, result.stderr, total_ms)

    # a bemeneti fájl megírása és optimalizálása; ha nincs megadva útvonal, a program mappájának notes.txt-jébe ír
    def optimize(self, open_strings, notes, input_path=None):
        if input_path is None:
            input_path = self.default_input_path()
        self.write_input(open_strings, notes, input_path)
        return self.run_file(input_path)

    # paraméter nélküli futtatás: a C++ program a benchmark tesztjeit futtatja, az eredményt a benchmark_results mappába írja
    def run_benchmark(self):
        return subprocess.run([str(self.cpp_exe)], cwd=str(self.cpp_exe.parent), capture_output=True, text=True)

    # a benchmark részletes eredményfájlja
    def benchmark_log_path(self):
        return self.paths.benchmark_results_dir / f"{self.algo}_benchmark_results.txt"

    # a benchmark összesítő fájlja (minden eljárás egy sora)
    def benchmark_summary_path(self):
        return self.paths.benchmark_results_dir / "osszesitett_eredmenyek.txt"
