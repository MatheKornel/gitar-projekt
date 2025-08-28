#Library importok
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import soundfile as sf

#Fájl importok
from filter import BandpassFilter
from audio_files import Audio
from spectrograms import Spectrogram
from note_recognition import ShortTimeFT

m = tk.Tk()
m.geometry("600x300")
m.title("Gitár projekt")

#Fájl betöltése és zajszűrés
def file_load():

    path = fd.askopenfilename(
        title="Fájl kiválasztása",
        filetypes=[("Hangfájl","*.mp3 *.wav")]
    )
    
    if path:
        original, fs = sf.read(path)
        print(f"Mintavételi frekvencia: {fs} Hz")

        if len(original.shape)>1:
            original = original.mean(axis=1)
    
        bpf = BandpassFilter(original)
        filtered = bpf.bandpass_filter(original, fs, lowcut=70, highcut=2800)
        output_path = path.replace(".wav", "_filtered.wav")
        sf.write(output_path, filtered, fs)
        print("Filtering done.")

        audio = Audio(original=original, filtered=filtered, fs=fs)
        global current_audio
        current_audio = audio

#Spektrogram megjelenítése a betöltött hanganyagból - szűrés előtti és utáni állapot
def show_spectrogram():
    global current_audio
    if current_audio:
        spec = Spectrogram(current_audio.original, current_audio.filtered, current_audio.fs)
    spec.spectrograms()

#STFT elvégzése
def show_note_rec():
    global current_audio
    if current_audio:
        stft = ShortTimeFT(current_audio.filtered)
    stft.note_rec(5)
        
#Alkalmazás dolgai
open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.place(x=0, y=0)
spectrogram_button = ttk.Button(m, text="Szűrés utáni összehasonlítás", command=show_spectrogram)
spectrogram_button.place(x=95, y=0)
note_rec_button = ttk.Button(m, text="STFT indítása", command=show_note_rec)
note_rec_button.place(x=255, y=0)

m.mainloop()
