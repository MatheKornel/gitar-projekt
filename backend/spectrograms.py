from audio_files import Audio
from scipy import signal
import numpy as np
import matplotlib.pyplot as plt

class Spectrogram:
    def __init__(self, original, filtered, fs):
        self.original = original
        self.filtered = filtered
        self.fs = fs
    
    def spectrograms(self):
        if self.original is None or self.filtered is None:
            print("Load a file!")
            return

        f1, t1, Sxx1 = signal.spectrogram(self.original, self.fs)
        f2, t2, Sxx2 = signal.spectrogram(self.filtered, self.fs)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

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