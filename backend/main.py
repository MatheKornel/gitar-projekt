#Library importok
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import soundfile as sf
import os
import librosa as lb
import numpy as np

#Fájl importok
from filter import BandpassFilter
from audio_files import Audio
from spectrograms import Spectrogram
from note_recognition import ShortTimeFT
from midi import MidiExporter
from sheet_music_exporter import SheetMusicExporter
from onset_histogram import OnsetHistogram
from onset_detect import OnsetDetect

m = tk.Tk()
m.geometry("700x300")
m.title("Gitár projekt")

current_audio = None
current_notes = None
original_filepath = ""
last_opened_dir = None
histogram = OnsetHistogram()

#Fájl betöltése és zajszűrés
def file_load():
    global current_audio, original_filepath, current_notes, last_opened_dir

    if last_opened_dir:
        start_dir = last_opened_dir
    else:
        start_dir = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.exists(start_dir):
            start_dir = os.path.expanduser("~")

    path = fd.askopenfilename(
        title="Fájl kiválasztása",
        initialdir=start_dir,
        filetypes=[("Hangfájl", "*.wav")]
    )
    
    if path:
        last_opened_dir = os.path.dirname(path)
        original_filepath = path
        print(f"Betöltött fájl: {os.path.basename(original_filepath)}")
        original, fs = sf.read(path)
        print(f"Mintavételi frekvencia: {fs} Hz")
        
        original = original.mean(axis=1) if len(original.shape) > 1 else original
    
        bpf = BandpassFilter(original)
        filtered = bpf.bandpass_filter(original, fs, lowcut=70, highcut=2800)
        print("Szűrés elvégezve.")

        audio = Audio(original=original, filtered=filtered, fs=fs)
        current_audio = audio
        current_notes = None # új fájl betöltésekor töröljük a korábbi adatokat

#Spektrogram megjelenítése a betöltött hanganyagból - szűrés előtti és utáni állapot
def show_spectrogram():
    global current_audio
    if current_audio:
        spec = Spectrogram(current_audio.original, current_audio.filtered, current_audio.fs)
    spec.spectrograms()

#STFT elvégzése
def show_note_rec():
    global current_audio, current_notes
    if current_audio:
        onset = OnsetDetect(current_audio.filtered, fs=current_audio.fs)
        stft = ShortTimeFT(current_audio.filtered)
        print("Elemzés folyamatban...")

        notes, envelope = stft.note_rec(5, histogram) # a hangok mellett az envelope-ot is visszaadja, hogy csak egyszer fusson le
        temp_onsets = onset.get_onsets(envelope, min_gap=0.05, prominence=0.2)
        histogram.calculate_iois(temp_onsets)
        histogram.find_optimal_gap()
        bpm = histogram.get_bpm() # minden eddigi hisztogramos számolás itt a BPM miatt kell

        bpm_entry.delete(0, tk.END)
        bpm_entry.insert(0, str(bpm))

        print(f"BPM becslés: {bpm} BPM")
        current_notes = notes
        if notes:
            print("Elemzés kész.")
        else:
            print("Nincsenek felismert hangok.")

# MIDI exportálás
def save_midi():
    global current_notes, original_filepath
    if not current_notes:
        print("Nincsenek felismert hangok a MIDI exportáláshoz.")
        return
    
    if not original_filepath:
        print("Nincs eredeti fájlnév a mentéshez.")
        return
    
    exporter = MidiExporter(tempo=int(bpm_entry.get()))
    base_name = os.path.basename(original_filepath)
    file_name = os.path.splitext(base_name)[0] + ".mid"
    output_midi_path = os.path.join("MIDI_files", file_name)

    exporter.create_midi(current_notes, output_midi_path)

# Kotta generálás és megjelenítés
def generate_sheet_music():
    global current_notes, original_filepath
    if not current_notes:
        print("Nincsenek felismert hangok a kottához.")
        return
    
    if not original_filepath:
        print("Nincs eredeti fájlnév a mentéshez.")
        return
    
    base_name = os.path.basename(original_filepath)
    file_name = os.path.splitext(base_name)[0]

    exporter = SheetMusicExporter(audio_tempo=int(bpm_entry.get()))
    pdf_path = exporter.create_score(current_notes, file_basename=file_name)

    if pdf_path:
        print(f"PDF generálva: {pdf_path}")
    else:
        print("Kotta generálása sikertelen.")



#Alkalmazás dolgai
open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.place(x=0, y=0)

spectrogram_button = ttk.Button(m, text="Szűrés utáni összehasonlítás", command=show_spectrogram)
spectrogram_button.place(x=95, y=0)

note_rec_button = ttk.Button(m, text="Hangfelismerés", command=show_note_rec)
note_rec_button.place(x=255, y=0)

midi_export_button = ttk.Button(m, text="MIDI exportálása", command=save_midi)
midi_export_button.place(x=350, y=0)

sheet_music_button = ttk.Button(m, text="Kotta generálása", command=generate_sheet_music)
sheet_music_button.place(x=450, y=0)

bpm_label = ttk.Label(m, text="BPM:")
bpm_label.place(x=0, y=30)
bpm_entry = ttk.Entry(m, width=5)
bpm_entry.insert(0, "120")
bpm_entry.place(x=30, y=30)

m.mainloop()
