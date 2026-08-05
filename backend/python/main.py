import os
import re
import subprocess
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk

import soundfile as sf

from audio_files import Audio
from config_paths import ProjectPaths
from config_parameters import ProjectConfig
from data_to_txt_converter import DataToTxtConverter
from filter import BandpassFilter
from midi import MidiExporter
from note_recognition import ShortTimeFT
from onset_histogram import OnsetHistogram
from sheet_music_tab_exporter import SheetMusicTabExporter
from spectrograms import Spectrogram


class GuitarProjectApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("700x300")
        self.root.title("Gitár projekt")

        self.current_audio = None
        self.current_notes = None
        self.original_filepath = ""
        self.last_opened_dir = None
        self.histogram = OnsetHistogram()
        self.paths = ProjectPaths()
        self.config = ProjectConfig()
        self.algo = ""
        self.select = tk.IntVar(value=1)
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
        if self.current_audio:
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

        self.tunings_combobox.current(0) # alapértelmezett hangolás: E

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
            original, fs = sf.read(path)
            print(f"Mintavételi frekvencia: {fs} Hz")

            original = original.mean(axis=1) if len(original.shape) > 1 else original

            bpf = BandpassFilter(original)
            filtered = bpf.bandpass_filter(original, fs, lowcut=self.config.filter_lowcut, highcut=self.config.filter_highcut)
            print("Szűrés elvégezve.")

            self.current_audio = Audio(original=original, filtered=filtered, fs=fs)
            self.current_notes = None
            self.is_note_rec_done = False
            self.refresh_ui()

    def show_spectrogram(self):
        if self.current_audio:
            spec = Spectrogram(self.current_audio.original, self.current_audio.filtered, self.current_audio.fs)
            spec.spectrograms()

    def show_note_rec(self):
        if not self.current_audio:
            return

        stft = ShortTimeFT(self.current_audio.filtered)
        print("Elemzés folyamatban...")

        notes = stft.note_rec(5, self.histogram)

        test_file_name = os.path.splitext(os.path.basename(self.original_filepath))[0] + "_test.txt"
        converter = DataToTxtConverter(notes, paths=self.paths)
        converter.save_to_test_txt(output_txt_path=test_file_name)

        bpm = self.histogram.get_bpm()
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

    def finger_optimization(self):
        if not self.current_notes:
            print("Nincsenek felismert hangok az optimalizáláshoz.")
            return

        if self.select.get() == 1:
            self.algo = "viterbi"
        elif self.select.get() == 2:
            self.algo = "pso"
        elif self.select.get() == 3:
            self.algo = "main"
        elif self.select.get() == 4:
            self.algo = "main_plus_viterbi"

        converter = DataToTxtConverter(self.current_notes, paths=self.paths)
        converter.save_note_to_txt(self.algo)

        cpp_exe = self.paths.cpp_executable(self.algo)
        if cpp_exe.exists():
            print("Ujjrend optimalizálás indítása...")
            txt_path = os.path.join(str(cpp_exe.parent), "notes.txt")
            result = subprocess.run([str(cpp_exe), txt_path], cwd=str(cpp_exe.parent), capture_output=True, text=True)
            print("C++ kimenet:")
            print(result.stdout)

            if result.returncode == 0:
                matches = re.findall(r'Hur:\s*([EADGBe])\s*Bund:\s*(\d+)', result.stdout)
                string_map = {'e': 1, 'B': 2, 'G': 3, 'D': 4, 'A': 5, 'E': 6}
                if matches:
                    if len(matches) != len(self.current_notes):
                        print(f"Figyelem: A C++ {len(matches)} sort adott vissza, de {len(self.current_notes)} hang van! A meglévők lesznek párosítva.")
                    for i, (hur_str, bund_str) in enumerate(matches):
                        if i < len(self.current_notes):
                            s_val = string_map.get(hur_str)
                            if s_val is not None:
                                self.current_notes[i].opt_string_num = s_val
                                self.current_notes[i].opt_fret_num = int(bund_str)
            if result.returncode != 0:
                print("C++ hiba:")
                print(result.stderr)
        else:
            print(f"Nem találom a {cpp_exe} fájlt!")

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

    def generate_sheet_music(self):
        if not self.current_notes:
            print("Nincsenek felismert hangok a kottához.")
            return

        if not self.original_filepath:
            print("Nincs eredeti fájlnév a mentéshez.")
            return

        base_name = os.path.basename(self.original_filepath)
        file_name = os.path.splitext(base_name)[0]

        exporter = SheetMusicTabExporter(audio_tempo=int(self.bpm_entry.get()), paths=self.paths, config=self.config)
        pdf_path = exporter.create_score(self.current_notes, file_basename=file_name)

        if pdf_path:
            print(f"PDF generálva: {pdf_path}")
        else:
            print("Kotta generálása sikertelen.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = GuitarProjectApp()
    app.run()
