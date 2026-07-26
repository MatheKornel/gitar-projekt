import os
import subprocess
import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk

import soundfile as sf

from audio_files import Audio
from config import ProjectPaths
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
        self.algo = ""
        self.select = tk.IntVar(value=1)

        self._build_ui()

    def _build_ui(self):
        open_button = ttk.Button(self.root, text="Fájl megnyitása", command=self.file_load)
        open_button.place(x=0, y=0)

        spectrogram_button = ttk.Button(self.root, text="Szűrés utáni összehasonlítás", command=self.show_spectrogram)
        spectrogram_button.place(x=95, y=0)

        note_rec_button = ttk.Button(self.root, text="Hangfelismerés", command=self.show_note_rec)
        note_rec_button.place(x=255, y=0)

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
            filtered = bpf.bandpass_filter(original, fs, lowcut=70, highcut=2800)
            print("Szűrés elvégezve.")

            self.current_audio = Audio(original=original, filtered=filtered, fs=fs)
            self.current_notes = None

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

        if self.select.get() == 1:
            self.algo = "viterbi"
        elif self.select.get() == 2:
            self.algo = "pso"

        converter = DataToTxtConverter(notes, paths=self.paths)
        converter.save_note_to_txt(self.algo)

        cpp_exe = self.paths.cpp_executable(self.algo)
        if cpp_exe.exists():
            print("Ujjrend optimalizálás indítása...")
            result = subprocess.run([str(cpp_exe)], cwd=str(cpp_exe.parent), capture_output=True, text=True)
            print("C++ kimenet:")
            print(result.stdout)
            if result.returncode != 0:
                print("C++ hiba:")
                print(result.stderr)
        else:
            print(f"Nem találom a {cpp_exe} fájlt!")

        test_file_name = os.path.splitext(os.path.basename(self.original_filepath))[0] + "_test.txt"
        converter.save_to_test_txt(output_txt_path=test_file_name)

        bpm = self.histogram.get_bpm()
        self.bpm_entry.delete(0, tk.END)
        self.bpm_entry.insert(0, str(bpm))

        print(f"BPM becslés: {bpm} BPM")
        self.current_notes = notes
        if notes:
            print("Elemzés kész.")
        else:
            print("Nincsenek felismert hangok.")

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

        exporter = SheetMusicTabExporter(audio_tempo=int(self.bpm_entry.get()))
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
