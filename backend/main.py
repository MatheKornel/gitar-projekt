import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import soundfile as sf
from filter import BandpassFilter
from audio_files import Audio
from spectrograms import Spectrogram

m = tk.Tk()
m.geometry("600x300")
m.title("Gitár projekt")

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

def show_spectrogram():
    global current_audio
    if current_audio:
        spec = Spectrogram(current_audio.original, current_audio.filtered, current_audio.fs)
    spec.spectrograms()
        

open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.place(x=0, y=0)
spectrogram_button = ttk.Button(m, text="Szűrés utáni összehasonlítás", command=show_spectrogram)
spectrogram_button.place(x=95, y=0)

m.mainloop()
