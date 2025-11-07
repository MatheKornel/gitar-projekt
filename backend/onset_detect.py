from stockwell import st
import numpy as np
import scipy.signal as sig
import librosa

class OnsetDetect:
    def __init__(self, filtered, fs = 44100):
        self.filtered = filtered
        self.fs = fs

    def onset_detect(self, min_gap = 0.3):

        # a magas mintavételi frekvenciát lecsökkentjük gyorsítás miatt
        if (self.fs > 8000):
            self.filtered = librosa.resample(self.filtered, orig_sr=self.fs, target_sr=8000)
            self.fs = 8000
        
        slice_duration_sec = 3.0 # 3 másodperces darabokat dolgozunk fel
        slice_samples = int(slice_duration_sec * self.fs)
        overlap_samples = int(min_gap * 2 * self.fs) # 2x minimális távolság átfedésként, hogy ne maradjon ki semmi
        step_samples = slice_samples - overlap_samples # lépésköz
        global_max = 1e-9 # globális maximum az envelope normalizálásához

        # globális maximum keresése a szeletelés miatt
        for start_sample in range(0, len(self.filtered) - overlap_samples, step_samples):
            end_sample = start_sample + slice_samples
            slice = self.filtered[start_sample:end_sample]
            if len(slice) < overlap_samples / 2:
                break

            S = st.st(slice, lo=75, hi=3000)
            S_mag = np.abs(S)

            Q = 10
            num_freqs = S_mag.shape[0]
            P = num_freqs // Q
            envelopes = [np.mean(S_mag[i * P:(i + 1) * P, :], axis=0) for i in range(Q)]
            env = np.sum(np.array(envelopes), axis=0)

            slice_max = np.max(env)
            if slice_max > global_max:
                global_max = slice_max

        all_onset_times = []

        # globális maximum után újra végigmegyünk a szeleteken az onset detektáláshoz
        for start_sample in range(0, len(self.filtered) - overlap_samples, step_samples):
            end_sample = start_sample + slice_samples
            slice = self.filtered[start_sample:end_sample]

            if len(slice) < overlap_samples / 2: # ha túl rövid a maradék darab, kihagyjuk
                break

            # maga az S-transzformáció a szeletre
            S = st.st(slice, lo=75, hi=3000)
            S_mag = np.abs(S)

            # frekvenciasávokra bontás és envelope készítés
            Q = 10
            num_freqs = S_mag.shape[0]
            P = num_freqs // Q
            envelopes = [np.mean(S_mag[i * P:(i + 1) * P, :], axis=0) for i in range(Q)]

            # összegezzük a sáv energiáját
            env = np.sum(np.array(envelopes), axis=0)

            # normalizáljuk a végső összeget
            env = env / global_max

            env_smooth = sig.medfilt(env, kernel_size=7)
            #env_smooth = np.convolve(env_smooth, np.ones(5)/5, mode='same')

            slice_total_duration_sec = len(slice) / self.fs # az szelet hossza másodpercben
            samples_per_sec_in_env = len(env_smooth) / slice_total_duration_sec # hány minta van másodpercenként az envelope-ban

            min_dist_samples = int(min_gap * samples_per_sec_in_env) # minimális távolság mintában
            # ha véletlen 0 lenne akkor legyen 1
            if min_dist_samples < 1:
                min_dist_samples = 1
            
            # csúcsdetektálás
            peaks, _ = sig.find_peaks(env_smooth, distance=min_dist_samples, prominence=0.1, height=0.05)

            # időpontok számítása
            slice_times = np.linspace(0, slice_total_duration_sec, len(env_smooth))
            slice_onset_times = slice_times[peaks]

            global_onset_times = slice_onset_times + (start_sample / self.fs) # globális időpontok
            all_onset_times.extend(global_onset_times)

        if not all_onset_times:
            return np.array([])
        
        # átfedés miatt lehetnek duplikálások, azok kiszűrése
        all_onset_times.sort()

        final_onset_times = [all_onset_times[0]]
        for t in all_onset_times[1:]:
            if t - final_onset_times[-1] > min_gap:
                final_onset_times.append(t)

        return np.array(final_onset_times)

