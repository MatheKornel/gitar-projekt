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

original = None
filtered = None
fs = None

def bandpass_filter(original, fs, lowcut, highcut, order=5):
    nyq = fs*0.5
    low = lowcut/nyq
    high = highcut/nyq
    b, a = signal.butter(order, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, original)
    return filtered

def file_load():
    global original, filtered, fs

    path = fd.askopenfilename(
        title="Fájl kiválasztása",
        filetypes=[("Hangfájl","*.mp3 *.wav")]
    )
    
    if path:
        original, fs = sf.read(path)
        print(f"Mintavételi frekvencia: {fs} Hz")

        if len(original.shape)>1:
            original=original.mean(axis=1)
    
    filtered = bandpass_filter(original, fs, lowcut=70, highcut=2800, )
    output_path = path.replace(".wav", "_filtered.wav")
    sf.write(output_path, filtered, fs)
    print("Filtering done.")

def spectrograms():
    global original, filtered, fs

    if original is None or filtered is None:
        print("Load a file!")
        return

    f1, t1, Sxx1 = signal.spectrogram(original, fs)
    f2, t2, Sxx2 = signal.spectrogram(filtered, fs)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.pcolormesh(t1, f1, 10*np.log10(Sxx1+1e-10), shading='gouraud')
    ax1.set_title("Eredeti jel spektrogramja")
    ax1.set_ylabel('Frekvencia [Hz]')
    ax1.set_xlabel('Idő [sec]')

    ax2.pcolormesh(t2, f2, 10*np.log10(Sxx2+1e-10), shading='gouraud')
    ax2.set_title("Szűrt jel spektrogramja")
    ax2.set_ylabel('Frekvencia [Hz]')
    ax2.set_xlabel('Idő [sec]')

    print("Spectrograms shown.")
    plt.tight_layout()
    plt.show()
        

open_button = ttk.Button(m, text="Fájl megnyitása", command=file_load)
open_button.pack()
spectrogram_button = ttk.Button(m, text="Szűrés utáni összehasonlítás", command=spectrograms)
spectrogram_button.pack()

m.mainloop()
