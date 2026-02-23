import numpy as np
import scipy.signal as sig
import librosa as lb

class OnsetDetect:
    def __init__(self, filtered, fs = 44100):
        self.filtered = filtered # szűrt audio jel
        self.fs = fs # mintavételi frekvencia
        self.envelope = None # onset envelope
        self.hop_length = 512 # ablaklépés

    def make_envelope(self):
        # spektrogram készítés STFT-vel (spectral flux miatt ez kell ST helyett)
        n_fft = 2048
        D = lb.stft(self.filtered, n_fft=n_fft, hop_length=self.hop_length)
        magnitude = np.abs(D)

        diff = np.diff(magnitude, axis=1) # spectral flux számítása
        diff_rectified = np.maximum(0, diff) # rektifikálás --> csak a pozitív változásokat vesszük figyelembe

        flux = np.sum(diff_rectified**2, axis=0) # energia összegzése minden frekvenciasávban (különbségek négyzetét összegezzük)
        self.envelope = np.insert(flux, 0, 0) # az első értékhez nincs előző, így oda 0-át teszünk

        if np.max(self.envelope) > 0:
            self.envelope /= np.max(self.envelope) # normalizálás a maxhoz
        
        return self.envelope
    
    def get_onsets(self, min_gap = 0.05):
        if self.envelope is None:
            self.make_envelope()
        
        times = lb.frames_to_time(np.arange(len(self.envelope)), sr=self.fs, hop_length=self.hop_length) # időbélyegek a frame-ekhez
        
        # adaptív küszöb
        median_window_time = 0.1
        median_window_frames = int(median_window_time * self.fs / self.hop_length)
        if median_window_frames % 2 == 0:
            median_window_frames += 1 # páratlan számú frame a mediánhoz (medfilt csak ezzel működik)

        local_median = sig.medfilt(self.envelope, kernel_size=median_window_frames) # lokális medián kiszámítása

        delta = 0.02 # csendes zajok kiszűrése miatt
        adaptive_threshold = local_median + delta # adaptív küszöb a lokális medián alapján

        min_gap = max(1, int(min_gap * self.fs / self.hop_length)) # minimum távolság frame-ekben

        peaks, _ = sig.find_peaks(self.envelope, height=adaptive_threshold, distance=min_gap) # csúcsok keresése a küszöb felett és a minimum távolság figyelembevételével
        onset_times = times[peaks]

        return onset_times
