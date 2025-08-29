import librosa as lb
import numpy as np
import statistics

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
        f0_candidates = []
        for i in range(len(dominant_freqs)):
            f0 = dominant_freqs[i]
            tau = fs/f0
            m = 0
            harmonics = []
            s = 1.0
            for j in range(max_harmonics):
                m += 1
                freq = m*(fs/tau)
                amp = 0.0
                for k in range(len(freqs)):
                    if (freqs[k] >= freq-4) and (freqs[k] <= freq+4):
                        amp += float(magnitude[k, i])
                salience = amp*s
                s = s/2
                harmonics.append((round(freq, 4), round(amp, 4), round(salience, 4)))
            #print(f"\nFrame {i}, f0={f0:.2f} Hz:")
            #for l, (f, a, t) in enumerate(harmonics):
            #    print(f"  Harmonic {l+1}: {f:.2f} Hz, amplitude={a:.2f}, salience={t:.2f}")
            max_salience = max(harmonics, key=lambda x: x[2])
            f0_candidates.append(max_salience[0])
        
        final_f0 = statistics.mode([round(f,1) for f in f0_candidates])
        
        def near_amp(freq):
            for k, f in enumerate(freqs):
                if abs(f - freq) <= 4:
                    if np.mean(magnitude[k]) > 0.1:
                        return True
            return False

        temp = final_f0
        best_f0 = final_f0
        while temp > 75:
            temp = temp/2
            if near_amp(temp):
                best_f0 = temp
            else:
                break

        print(f"f0 = {best_f0:.2f} Hz")



        
        
