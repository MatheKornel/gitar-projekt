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

        # végigmegyünk az összes sávon és megkeressük a globális maximumot az összes sáv összes ideje közül
        all_envs = np.array(envelopes[0:8]) 
        global_max = np.max(all_envs) + 1e-9
        # mindent ehhez normalizálunk
        normalized_envelopes = all_envs / global_max

        # vesszük a sávok maximumát és conclove nélkül, hogy a halk csúcsokat is megtaláljuk
        env = np.max(normalized_envelopes, axis=0)
        env_smooth = sig.medfilt(env, kernel_size=7)
        #env_smooth = np.convolve(env_smooth, np.ones(5)/5, mode='same')

        total_duration_sec = len(self.filtered) / self.fs # az egész jel hossza másodpercben
        samples_per_sec_in_env = len(env_smooth) / total_duration_sec # hány minta van másodpercenként az envelope-ban

        min_dist_samples = int(min_gap * samples_per_sec_in_env) # minimális távolság mintában
        # ha véletlen 0 lenne akkor legyen 1
        if min_dist_samples < 1:
            min_dist_samples = 1
        
        # Csúcsdetektálás
        peaks, _ = sig.find_peaks(env_smooth, distance=min_dist_samples, prominence=0.08, height=0.05)

        # Időpontok számítása
        times = np.linspace(0, total_duration_sec, len(env_smooth))
        onset_times = times[peaks]
        return onset_times

