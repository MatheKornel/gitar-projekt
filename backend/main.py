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

m = tk.Tk()
m.geometry("700x300")
m.title("Gitár projekt")

current_audio = None
current_notes = None
current_tempo = 120
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

        if len(original.shape)>1:
            original = original.mean(axis=1)
    
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
    global current_audio, current_notes, current_tempo
    if current_audio:
        tempo, _ = lb.beat.beat_track(y=current_audio.filtered, sr=current_audio.fs)
        current_tempo = round(np.mean(tempo))
        stft = ShortTimeFT(current_audio.filtered)
        notes = stft.note_rec(5, current_tempo, histogram)
        current_notes = notes
        if notes:
            print("Elemzés kész.")
        else:
            print("Nincsenek felismert hangok.")

# MIDI exportálás
def save_midi():
    global current_notes, original_filepath, current_tempo
    if not current_notes:
        print("Nincsenek felismert hangok a MIDI exportáláshoz.")
        return
    
    if not original_filepath:
        print("Nincs eredeti fájlnév a mentéshez.")
        return
    
    exporter = MidiExporter(tempo=current_tempo)
    base_name = os.path.basename(original_filepath)
    file_name = os.path.splitext(base_name)[0] + ".mid"
    output_midi_path = os.path.join("MIDI_files", file_name)

    exporter.create_midi(current_notes, output_midi_path)

# Kotta generálás és megjelenítés
def generate_sheet_music():
    global current_notes, original_filepath, current_tempo
    if not current_notes:
        print("Nincsenek felismert hangok a kottához.")
        return
    
    if not original_filepath:
        print("Nincs eredeti fájlnév a mentéshez.")
        return
    
    base_name = os.path.basename(original_filepath)
    file_name = os.path.splitext(base_name)[0]

    exporter = SheetMusicExporter(audio_tempo=current_tempo)
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

histogram_button = ttk.Button(m, text="Onset hisztogram", command=histogram.show_histogram)
histogram_button.place(x=550, y=0)

m.mainloop()
