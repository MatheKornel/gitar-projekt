import io
import os
import sys
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk

from audio_files import Audio
from config_paths import ProjectPaths
from config_parameters import ProjectConfig
from cpp_optimizer import CppOptimizer
from data_to_txt_converter import DataToTxtConverter
from midi import MidiExporter
from onset_histogram import OnsetHistogram
from recognition_pipeline import load_audio, recognize
from sheet_music_tab_exporter import SheetMusicTabExporter
from spectrograms import Spectrogram
from guitar_note_freqs import GuitarNoteFreqs


class GuitarProjectApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("700x300")
        self.root.title("Gitár projekt")

        self.original_audio = None
        self.fs = None
        self.current_audio = None
        self.current_notes = None
        self.original_filepath = ""
        self.last_opened_dir = None
        self.histogram = OnsetHistogram()
        self.paths = ProjectPaths()
        self.config = ProjectConfig()
        self.algo = ""
        self.select = tk.IntVar(value=3)
        self.is_note_rec_done = False

        self._build_ui()
        self.refresh_ui()

    def _build_ui(self):
        open_button = ttk.Button(self.root, text="Fájl megnyitása", command=self.file_load)
        open_button.place(x=0, y=0)

        spectrogram_button = ttk.Button(self.root, text="Szűrés utáni összehasonlítás", command=self.show_spectrogram)
        spectrogram_button.place(x=95, y=0)

        note_rec_button = ttk.Button(self.root, text="Hangfelismerés", command=self.show_note_rec)
        note_rec_button.place(x=255, y=0)

        opt_button = ttk.Button(self.root, text="Ujjrend optimalizálás", command=self.finger_optimization)
        opt_button.place(x=255, y=30)

        opt_benchmark_button = ttk.Button(self.root, text="Ujjrend benchmark", command=self.finger_optimization_benchmark)
        opt_benchmark_button.place(x=390, y=30)

        midi_export_button = ttk.Button(self.root, text="MIDI exportálása", command=self.save_midi)
        midi_export_button.place(x=350, y=0)

        sheet_music_button = ttk.Button(self.root, text="Kotta generálása", command=self.generate_sheet_music)
        sheet_music_button.place(x=450, y=0)

        bpm_label = ttk.Label(self.root, text="BPM:")
        bpm_label.place(x=0, y=30)
        self.bpm_entry = ttk.Entry(self.root, width=5)
        self.bpm_entry.insert(0, "120")
        self.bpm_entry.place(x=30, y=30)

        opt_label = ttk.Label(self.root, text="Optimalizáló eljárás:")
        opt_label.place(x=0, y=60)
        r1 = ttk.Radiobutton(self.root, text="Viterbi algoritmus", variable=self.select, value=1)
        r1.place(x=0, y=80)
        r2 = ttk.Radiobutton(self.root, text="PSO algoritmus", variable=self.select, value=2)
        r2.place(x=0, y=100)
        r3 = ttk.Radiobutton(self.root, text="Saját algoritmus", variable=self.select, value=3)
        r3.place(x=0, y=120)
        r4 = ttk.Radiobutton(self.root, text="Saját + Viterbi algoritmus", variable=self.select, value=4)
        r4.place(x=0, y=140)

        tuning_label = ttk.Label(self.root, text="Hangolás:")
        tuning_label.place(x=100, y=30)
        tunings = ["E", "D# / Eb", "D", "C# / Db", "C", "B", "A# / Bb", "A", "G# / Ab", "G", "F# / Gb", "F"]
        self.tunings_combobox = ttk.Combobox(self.root, values=tunings, state="readonly", width=7)
        self.tunings_combobox.current(0)
        self.tunings_combobox.place(x=160, y=30)

    def refresh_ui(self):
        if self.original_audio is not None:
            loaded_file_text = f"Betöltött fájl: {os.path.basename(self.original_filepath)}"
        else:
            loaded_file_text = "Betöltött fájl: nincs"

        loaded_file_label = ttk.Label(self.root, text=loaded_file_text)
        loaded_file_label.place(x=0, y=180)

        if self.is_note_rec_done:
            is_note_rec_done_text = "Hangfelismerés: kész"
        else:
            is_note_rec_done_text = "Hangfelismerés: nincs"

        is_note_rec_done_label = ttk.Label(self.root, text=is_note_rec_done_text)
        is_note_rec_done_label.place(x=0, y=200)

    def file_load(self):
        if self.last_opened_dir:
            start_dir = self.last_opened_dir
        else:
            start_dir = os.path.join(os.path.expanduser("~"), "Music")
            if not os.path.exists(start_dir):
                start_dir = os.path.expanduser("~")

        path = fd.askopenfilename(
            title="Fájl kiválasztása",
            initialdir=start_dir,
            filetypes=[("Hangfájl", "*.wav")],
        )

        if path:
            self.last_opened_dir = os.path.dirname(path)
            self.original_filepath = path
            print(f"Betöltött fájl: {os.path.basename(self.original_filepath)}")
            original, fs = load_audio(path)
            print(f"Mintavételi frekvencia: {fs} Hz")
            self.fs = fs

            self.original_audio = original
            self.current_notes = None
            self.is_note_rec_done = False
            self.refresh_ui()
            self.tunings_combobox.current(0) # alapértelmezett hangolás: E

    def show_spectrogram(self):
        if self.current_audio is not None:
            spec = Spectrogram(self.current_audio.original, self.current_audio.filtered, self.current_audio.fs)
            spec.spectrograms()

    def show_note_rec(self):
        if self.original_audio is None or self.fs is None:
            return

        filtered, notes, bpm = recognize(self.original_audio, self.fs, self.tunings_combobox.get(), self.histogram)
        self.current_audio = Audio(original=self.original_audio, filtered=filtered, fs=self.fs)

        test_file_name = os.path.splitext(os.path.basename(self.original_filepath))[0] + "_test.txt"
        converter = DataToTxtConverter(notes, paths=self.paths)
        converter.save_to_test_txt(output_txt_path=test_file_name)

        self.bpm_entry.delete(0, tk.END)
        self.bpm_entry.insert(0, str(bpm))

        print(f"BPM becslés: {bpm} BPM")
        self.current_notes = notes
        if notes:
            print("Elemzés kész.")
            self.is_note_rec_done = True
            self.refresh_ui()
        else:
            print("Nincsenek felismert hangok.")
            self.is_note_rec_done = False
            self.refresh_ui()

    def _select_algo(self):
        # a kiválasztott rádiógomb alapján beállítja az optimalizáló eljárás nevét
        if self.select.get() == 1:
            self.algo = "viterbi"
        elif self.select.get() == 2:
            self.algo = "pso"
        elif self.select.get() == 3:
            self.algo = "main"
        elif self.select.get() == 4:
            self.algo = "main_plus_viterbi"

    def finger_optimization(self):
        if not self.current_notes:
            print("Nincsenek felismert hangok az optimalizáláshoz.")
            return

        self._select_algo()

        optimizer = CppOptimizer(self.algo, self.paths)
        if not optimizer.exists():
            print(f"Nem találom a {optimizer.cpp_exe} fájlt!")
            return

        print(f"\n[{self.algo}] Ujjrend optimalizálás indítása...")
        open_strings = GuitarNoteFreqs.open_string_midis(self.tunings_combobox.get())
        result = optimizer.optimize(open_strings, CppOptimizer.notes_from_events(self.current_notes))
        print("C++ kimenet:")
        print(result.stdout)

        if result.returncode != 0:
            print("C++ hiba:")
            print(result.stderr)
            return

        if result.optimization_ms is not None:
            print(f"Optimalizálás ideje: {result.optimization_ms:.2f} ms")
        if result.other_stderr():
            print("C++ figyelmeztetés:")
            print(result.other_stderr())

        if len(result.positions) != len(self.current_notes):
            print(f"Figyelem: A C++ {len(result.positions)} sort adott vissza, de {len(self.current_notes)} hang van! A meglévők lesznek párosítva.")
        for i in range(min(len(result.positions), len(self.current_notes))):
            string_num, fret = result.positions[i]
            self.current_notes[i].opt_string_num = string_num
            self.current_notes[i].opt_fret_num = fret

    def finger_optimization_benchmark(self):
        # a kiválasztott eljárás benchmarkja, nem kell hozzá betöltött fájl vagy hangfelismerés
        self._select_algo()

        optimizer = CppOptimizer(self.algo, self.paths)
        if not optimizer.exists():
            print(f"Nem találom a {optimizer.cpp_exe} fájlt!")
            return

        print(f"\n[{self.algo}] Benchmark tesztek indítása...")
        bench_result = optimizer.run_benchmark()
        print(bench_result.stdout)
        if bench_result.stderr:
            print("Benchmark figyelmeztetés / hiba:")
            print(bench_result.stderr)

    def save_midi(self):
        if not self.current_notes:
            print("Nincsenek felismert hangok a MIDI exportáláshoz.")
            return

        if not self.original_filepath:
            print("Nincs eredeti fájlnév a mentéshez.")
            return

        exporter = MidiExporter(tempo=int(self.bpm_entry.get()), paths=self.paths)
        base_name = os.path.basename(self.original_filepath)
        file_name = os.path.splitext(base_name)[0] + ".mid"
        exporter.create_midi(self.current_notes, file_name)

    def generate_sheet_music(self, open_pdf=True):
        if not self.current_notes:
            print("Nincsenek felismert hangok a kottához.")
            return

        if not self.original_filepath:
            print("Nincs eredeti fájlnév a mentéshez.")
            return

        base_name = os.path.basename(self.original_filepath)
        file_name = os.path.splitext(base_name)[0]

        exporter = SheetMusicTabExporter(audio_tempo=int(self.bpm_entry.get()), paths=self.paths, config=self.config)
        pdf_path = exporter.create_score(self.current_notes, file_basename=file_name, tuning=self.tunings_combobox.get(), open_pdf=open_pdf)

        if pdf_path:
            print(f"PDF generálva: {pdf_path}")
        else:
            print("Kotta generálása sikertelen.")

    def run(self):
        self.root.mainloop()

    def run_smoke_test(self, wav_path):
        """A teljes folyamat GUI kattintás nélkül, a release csomag ellenőrzéséhez.

        Hangfelismerés -> ujjrend optimalizálás (Saját) -> MIDI -> PDF kotta.
        Visszatérési érték: 0, ha minden kimenet létrejött, különben 1.
        """
        errors = []
        try:
            self.original_filepath = os.path.abspath(wav_path)
            self.original_audio, self.fs = load_audio(self.original_filepath)

            self.show_note_rec()
            if not self.current_notes:
                errors.append("nincsenek felismert hangok")
            else:
                self.select.set(3)
                self.finger_optimization()
                if not any(n.opt_string_num for n in self.current_notes):
                    errors.append("az ujjrend optimalizálás nem adott eredményt")

                self.save_midi()
                base = os.path.splitext(os.path.basename(self.original_filepath))[0]
                if not self.paths.output_path(base + ".mid", kind="midi").is_file():
                    errors.append("nem jött létre a MIDI fájl")

                self.generate_sheet_music(open_pdf=False)
                if not self.paths.output_path(base + ".pdf", kind="sheet").is_file():
                    errors.append("nem jött létre a PDF kotta")
        except Exception as e:
            errors.append(f"kivétel: {e!r}")
        finally:
            self.root.destroy()

        if errors:
            print("SMOKE TEST HIBA: " + "; ".join(errors))
            return 1
        print("SMOKE TEST OK")
        return 0


def _utf8_console_output():
    # Github actions miatt kell, UTF-8-ban nem dob hibát
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _utf8_console_output()
    app = GuitarProjectApp()
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        sys.exit(app.run_smoke_test(sys.argv[2]))
    app.run()
