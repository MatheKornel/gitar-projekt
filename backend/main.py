import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import scipy
from scipy import signal
import soundfile as sf
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

m = tk.Tk()
m.geometry("1000x600")
m.title("Gitár projekt")

def bandpass_filter(data, fs, lowcut, highcut, order=5):
    nyq = fs*0.5
    low = lowcut/nyq
    high = highcut/nyq
    b, a = signal.butter(order, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, data)
    return filtered

def file_load():
    path = fd.askopenfilename(
        title="Fájl kiválasztása",
        filetypes=[("Hangfájl","*.mp3 *.wav")]
    )

    if path:
        data, fs = sf.read(path)
        print(f"Mintavételi frekvencia: {fs}")

        if len(data.shape)>1:
            data=data.mean(axis=1)
    
    filtered = bandpass_filter(data, fs, lowcut=70, highcut=2800, )
    output_path = path.replace(".wav", "_filtered.wav")
    sf.write(output_path, filtered, fs)
    print("Filtering done.")
        

open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.pack()

m.mainloop()
