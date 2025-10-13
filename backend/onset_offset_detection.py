from stockwell import st
import numpy as np
import scipy.signal as sig
import librosa

class OnsetOffsetDetection:
    def __init__(self, filtered, fs = 44100):
        self.filtered = filtered
        self.fs = fs

    def onset_detect(self, min_gap = 0.3):

        # A magas mintavételi frekvenciát lecsökkentjük gyorsítás miatt
        if (self.fs > 8000):
            self.filtered = librosa.resample(self.filtered, orig_sr=self.fs, target_sr=8000)
            self.fs = 8000

        # Maga az S-transzformáció
        S = st.st(self.filtered, lo=75, hi=1350)
        S_mag = np.abs(S)

        # Frekvenciasávokra bontás és envelope készítés
        Q = 10
        num_freqs = S_mag.shape[0]
        P = num_freqs // Q
        envelopes = [np.mean(S_mag[i * P:(i + 1) * P, :], axis=0) for i in range(Q)]

        # Középső sávokat átlagoljuk
        env = np.mean(envelopes[3:7], axis=0)
        env = env / np.max(env)
        env_smooth = sig.medfilt(env, kernel_size=9)
        env_smooth = np.convolve(env_smooth, np.ones(5)/5, mode='same')

        # Csúcskeresés
        min_distance = int(self.fs * 0.05)
        peaks, _ = sig.find_peaks(env_smooth, distance=min_distance, prominence=0.25)
        times = np.linspace(0, len(self.filtered) / self.fs, len(env_smooth))
        onset_times = times[peaks]

        # Szűrés minimális időköz alapján
        filtered_onsets = [onset_times[0]]
        for t in onset_times[1:]:
            if t - filtered_onsets[-1] > min_gap:
                filtered_onsets.append(t)
        onset_times = np.array(filtered_onsets)

        return onset_times