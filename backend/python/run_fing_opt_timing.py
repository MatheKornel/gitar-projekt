import argparse
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
from config_paths import ProjectPaths

ALGOS = ['main', 'main_plus_viterbi', 'viterbi', 'pso']
SCALING_SIZES = [100, 250, 500, 1000, 2500, 5000, 10000]
STANDARD_E = [40, 45, 50, 55, 59, 64]
TEST_GAP = 1.0  # szünet (mp) az összefűzött tesztek között, hogy ne legyen irreálisan gyors váltás két teszt határán


class FingOptTiming:
    def __init__(self, paths, algo="main", repeats=10):
        self.paths = paths
        self.algo = algo
        self.repeats = repeats
        self.cpp_exe = paths.cpp_executable(algo)
        self.benchmark_dir = paths.repo_root / "benchmarks"
        self.temp_dir = tempfile.mkdtemp(prefix="fing_opt_timing_")
        self.test_results = []     # (teszt neve, hangok száma, optimalizálás átlag, szórás, teljes átlag, szórás)
        self.scaling_results = []  # (hangok száma, hanganyag hossza, optimalizálás átlag, szórás, teljes átlag, szórás)

    # benchmark fájl beolvasása: hangolás + hangok (midi, onset, duration, name)
    def load_benchmark_case(self, file_path):
        tuning = list(STANDARD_E)
        notes = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# tuning:"):
                    values = line[len("# tuning:"):].split()
                    if len(values) == 6:
                        tuning = [int(v) for v in values]
                    continue
                if not line or line.startswith("#") or line.startswith("MIDI"):
                    continue
                parts = line.split()
                notes.append((int(parts[0]), float(parts[1]), float(parts[2]), parts[3]))
        return tuning, notes

    # notes.txt formátumú bemenet írása (az alkalmazás saját notes.txt-je nem íródik felül)
    def write_input(self, tuning, notes, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(" ".join(str(m) for m in tuning) + "\n")
            f.write(f"{len(notes)}\n")
            for midi, onset, duration, name in notes:
                f.write(f"{midi} {onset:.4f} {duration:.4f} {name}\n")

    # egy futtatás: teljes idő (Python, indítástól a kimenet beolvasásáig) és a C++ által mért optimalizálási idő, ms-ban
    def run_once(self, file_path, note_count):
        start = time.perf_counter()
        result = subprocess.run([str(self.cpp_exe), file_path], cwd=str(self.cpp_exe.parent), capture_output=True, text=True)
        total_ms = (time.perf_counter() - start) * 1000.0

        if result.returncode != 0:
            raise RuntimeError(f"A C++ program hibával állt le:\n{result.stderr}")

        match = re.search(r"Optimalizalas ideje:\s*([0-9.eE+-]+)\s*ms", result.stderr)
        if match is None:
            raise RuntimeError("Nincs optimalizálási idő a C++ kimenetében, újra kell fordítani a programot!")

        positions = re.findall(r"Hur:\s*\S+\s*Bund:\s*\d+", result.stdout)
        if len(positions) != note_count:
            print(f"[!] Figyelem: {note_count} hang helyett {len(positions)} lefogás jött vissza.")

        return float(match.group(1)), total_ms

    # egy bemenet mérése: 1 bemelegítő futás (eldobjuk), utána repeats darab futás átlaga és szórása
    def measure(self, file_path, note_count):
        self.run_once(file_path, note_count)
        opt_times = []
        total_times = []
        for _ in range(self.repeats):
            opt_ms, total_ms = self.run_once(file_path, note_count)
            opt_times.append(opt_ms)
            total_times.append(total_ms)
        opt_std = statistics.stdev(opt_times) if len(opt_times) > 1 else 0.0
        total_std = statistics.stdev(total_times) if len(total_times) > 1 else 0.0
        return statistics.mean(opt_times), opt_std, statistics.mean(total_times), total_std

    def benchmark_files(self):
        files = []
        for name in sorted(os.listdir(self.benchmark_dir)):
            if name.endswith("_fing-opt_test.txt"):
                files.append(name)
        return files

    # 1. mérés: a benchmark tesztjei egyenként
    def measure_benchmark_tests(self):
        input_path = os.path.join(self.temp_dir, "timing_notes.txt")
        for name in self.benchmark_files():
            tuning, notes = self.load_benchmark_case(self.benchmark_dir / name)
            self.write_input(tuning, notes, input_path)
            opt_ms, opt_std, total_ms, total_std = self.measure(input_path, len(notes))
            test_name = name.replace("_fing-opt_test.txt", "")
            self.test_results.append((test_name, len(notes), opt_ms, opt_std, total_ms, total_std))
            print(f"  {test_name}: {len(notes)} hang, optimalizálás {opt_ms:.3f} ms, teljes {total_ms:.1f} ms")

    # hosszú bemenet: az E hangolású tesztek egymás után fűzve, az onseteket az előző teszt vége + szünet tolja el
    # ha kevés a hang, a tesztek sora körbeismétlődik
    def build_long_input(self, note_count):
        cases = []
        for name in self.benchmark_files():
            tuning, notes = self.load_benchmark_case(self.benchmark_dir / name)
            if tuning == STANDARD_E and notes:
                cases.append(notes)

        long_notes = []
        time_shift = 0.0
        while len(long_notes) < note_count:
            for notes in cases:
                first_onset = notes[0][1]
                end_time = time_shift
                for midi, onset, duration, name in notes:
                    if len(long_notes) >= note_count:
                        break
                    new_onset = time_shift + (onset - first_onset)
                    long_notes.append((midi, new_onset, duration, name))
                    end_time = max(end_time, new_onset + duration)
                time_shift = end_time + TEST_GAP
                if len(long_notes) >= note_count:
                    break

        last = long_notes[-1]
        audio_length = last[1] + last[2]  # az utolsó hang vége = a "hanganyag" hossza
        return long_notes, audio_length

    # 2. mérés: egyre hosszabb bemenetek
    def measure_scaling(self, sizes):
        input_path = os.path.join(self.temp_dir, "timing_long_notes.txt")
        for size in sizes:
            notes, audio_length = self.build_long_input(size)
            self.write_input(STANDARD_E, notes, input_path)
            opt_ms, opt_std, total_ms, total_std = self.measure(input_path, len(notes))
            self.scaling_results.append((size, audio_length, opt_ms, opt_std, total_ms, total_std))
            print(f"  {size} hang ({audio_length:.1f} s): optimalizálás {opt_ms:.3f} ms, teljes {total_ms:.1f} ms")

    # az ideiglenes bemeneti fájlok törlése
    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # eredmények szöveges táblázatai
    def results_text(self):
        lines = []
        lines.append(f"[{self.algo}] TESZTENKENTI FUTASIDO ({self.repeats} futas atlaga, ms)")
        lines.append(f"{'Teszt':<50} | {'Hangok':>6} | {'Optimalizalas':>13} | {'Szoras':>8} | {'Teljes':>8} | {'Szoras':>7}")
        for test_name, count, opt_ms, opt_std, total_ms, total_std in self.test_results:
            lines.append(f"{test_name:<50} | {count:>6} | {opt_ms:>13.3f} | {opt_std:>8.3f} | {total_ms:>8.1f} | {total_std:>7.1f}")

        lines.append("")
        lines.append(f"[{self.algo}] SKALAZAS ({self.repeats} futas atlaga, ms)")
        lines.append(f"{'Hangok':>6} | {'Hossz (s)':>9} | {'Optimalizalas':>13} | {'Szoras':>8} | {'Teljes':>8} | {'Szoras':>7} | {'Opt/hang (us)':>13} | {'Valos ideju szorzo':>18}")
        for count, length, opt_ms, opt_std, total_ms, total_std in self.scaling_results:
            per_note_us = opt_ms * 1000.0 / count
            realtime_factor = length / (total_ms / 1000.0)  # hányszor gyorsabb a feldolgozás a hanganyag hosszánál
            lines.append(f"{count:>6} | {length:>9.1f} | {opt_ms:>13.3f} | {opt_std:>8.3f} | {total_ms:>8.1f} | {total_std:>7.1f} | {per_note_us:>13.2f} | {realtime_factor:>18.0f}")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Az ujjrend optimalizálók futásidejének mérése.")
    parser.add_argument("-a", "--algo", default="all", choices=ALGOS + ['all'],
                        help="A mérendő eljárás ('all' esetén mind a négy).")
    parser.add_argument("-r", "--repeats", type=int, default=10, help="Hány futás átlaga legyen egy mérés.")
    args = parser.parse_args()

    paths = ProjectPaths()
    algos = ALGOS if args.algo == 'all' else [args.algo]

    texts = []
    for algo in algos:
        timing = FingOptTiming(paths, algo, args.repeats)
        if not timing.cpp_exe.exists():
            print(f"[!] Hiba: Nem talalhato a futtathato fajl: {timing.cpp_exe}")
            continue
        print(f"[{algo.upper()}] Tesztenkénti mérés...")
        timing.measure_benchmark_tests()
        print(f"[{algo.upper()}] Skálázási mérés...")
        timing.measure_scaling(SCALING_SIZES)
        timing.cleanup()
        texts.append(timing.results_text())

    result_path = paths.repo_root / "benchmark_results" / "futasido_eredmenyek.txt"
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(texts) + "\n")

    print("\n" + "\n\n".join(texts))
    print(f"\nEredmények mentve: {result_path}")


if __name__ == "__main__":
    main()
