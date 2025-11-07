#Library importok
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import soundfile as sf
import os

#Fájl importok
from filter import BandpassFilter
from audio_files import Audio
from spectrograms import Spectrogram
from note_recognition import ShortTimeFT
from midi import MidiExporter

m = tk.Tk()
m.geometry("600x300")
m.title("Gitár projekt")

current_audio = None
current_notes = None
original_filepath = ""

#Fájl betöltése és zajszűrés
def file_load():
    global current_audio, original_filepath, current_notes

    path = fd.askopenfilename(
        title="Fájl kiválasztása",
        filetypes=[("Hangfájl","*.mp3 *.wav")]
    )
    
    if path:
        original_filepath = path
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
    global current_audio, current_notes
    if current_audio:
        stft = ShortTimeFT(current_audio.filtered)
        notes = stft.note_rec(5)
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
    
    exporter = MidiExporter(tempo=120)
    base_name = os.path.basename(original_filepath)
    file_name = os.path.splitext(base_name)[0] + ".mid"
    output_midi_path = os.path.join("MIDI_files", file_name)

    exporter.create_midi(current_notes, output_midi_path)
        
#Alkalmazás dolgai
open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.place(x=0, y=0)
spectrogram_button = ttk.Button(m, text="Szűrés utáni összehasonlítás", command=show_spectrogram)
spectrogram_button.place(x=95, y=0)
note_rec_button = ttk.Button(m, text="STFT indítása", command=show_note_rec)
note_rec_button.place(x=255, y=0)
midi_export_button = ttk.Button(m, text="MIDI exportálása", command=save_midi)
midi_export_button.place(x=338, y=0)

m.mainloop()
