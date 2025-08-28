import librosa as lb
import numpy as np

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered

    def note_rec(self, max_harmonics):
        nfft = 2048
        fs = 44100

        #STFT
        D = lb.stft(self.filtered, n_fft=nfft, hop_length=512, window="hamming", center=False)
        freqs = lb.fft_frequencies(sr=44100, n_fft=nfft)
        magnitude = np.abs(D)
        dominant_bins = magnitude.argmax(axis=0)
        dominant_freqs = freqs[dominant_bins]

        #HS
        for i in range(len(dominant_freqs)):
            f0 = dominant_freqs[i]
            tau = fs/f0
            m = 0
            harmonics = []
            s = 1.0
            for j in range(max_harmonics):
                m += 1
                freq = m*(fs/tau)
                for k in range(len(freqs)):
                    if (freqs[k] >= freq-3) and (freqs[k] <= freq+3):
                        amp = float(magnitude[k, i])
                salience = amp*s
                s-=0.1
                harmonics.append((round(freq, 4), round(amp, 4), round(salience, 4)))
            print(f"\nFrame {i}, f0={f0:.2f} Hz:")
            for l, (f, a, t) in enumerate(harmonics):
                print(f"  Harmonic {l+1}: {f:.2f} Hz, amplitude={a:.2f}, salience={t:.2f}")

        



        
        
