from stockwell import st
import numpy as np
import scipy.signal as sig
import librosa as lb

class OnsetDetect:
    def __init__(self, filtered, fs = 44100):
        self.filtered = filtered
        self.fs = fs
        self.envelope = None

    def make_envelope(self):
        # a magas mintavételi frekvenciát lecsökkentjük gyorsítás miatt
        if (self.fs > 8000):
            self.filtered = lb.resample(self.filtered, orig_sr=self.fs, target_sr=8000)
            self.fs = 8000

        slice_duration_sec = 3.0 # 3 másodperces darabokat dolgozunk fel
        slice_samples = int(slice_duration_sec * self.fs)
        overlap_samples = int(0.5 * self.fs)
        step_samples = slice_samples - overlap_samples # lépésköz
        global_max = 1e-9 # globális maximum az envelope normalizálásához
        full_envelope = []

        current_sample = 0
        while current_sample < len(self.filtered) - overlap_samples:
            end_sample = current_sample + slice_samples
            audio_slice = self.filtered[current_sample:end_sample]
            if len(audio_slice) < slice_samples / 2:
                break
            
            # maga az S-transzformáció a szeletre
            S = st.st(audio_slice, lo=75, hi=3000)
            S_mag = np.abs(S)
            # frekvenciasávokra bontás és envelope készítés
            Q = 10
            num_freqs = S_mag.shape[0]
            P = num_freqs // Q
            env_slice = np.zeros(S_mag.shape[1])
            for i in range(Q):
                band = S_mag[i * P:(i + 1) * P, :]
                env_slice += np.mean(band, axis=0)
            
            current_max = np.max(env_slice)
            if current_max > global_max:
                global_max = current_max
            
            valid_part = env_slice[:step_samples]
            full_envelope.append(valid_part)
            current_sample += step_samples
        
        self.envelope = np.concatenate(full_envelope)
        self.envelope = self.envelope / global_max
        self.envelope = sig.medfilt(self.envelope, kernel_size=7)
        return self.envelope
    
    def get_onsets(self, min_gap = 0.2):
        min_dist_samples = int(min_gap * self.fs) # minimális távolság mintában
        # ha véletlen 0 lenne akkor legyen 1
        if min_dist_samples < 1:
            min_dist_samples = 1

        # csúcsdetektálás
        peaks, _ = sig.find_peaks(self.envelope, distance=min_dist_samples, prominence=0.05, height=0.02)
        onset_times = peaks / self.fs
        return onset_times

