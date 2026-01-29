import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

class OnsetHistogram:
    def __init__(self):
        self.onsets = None # onset időpontok mp-ben
        self.iois = [] # ioi-k
        self.optimal_gap = 0.35 # optimális min_gap
        self.bin_edges = None # hisztogram bin élek
        self.hist = None # hisztogram értékek
        self.smooth_hist = None # simított hisztogram értékek
        self.peaks = None # hisztogram csúcsok indexei
        self.bin_centers = None # hisztogram bin közepek
        self.last_optimal_gap = 0.35 # előző optimális min_gap
        self.dominant_interval = 0.5 # domináns intervallum mp-ben

    # IOI --> Inter-Onset Intervals kiszámítása --> szomszédos hangok távolsága
    def calculate_iois(self, onsets, min = 0.05, max = 1.0):
        self.onsets = np.array(onsets)
        if len(self.onsets) < 2:
            return []
        diffs = np.diff(self.onsets)
        self.iois = diffs[(diffs >= min) & (diffs <= max)]
        return self.iois
    
    # az optimális min_gap meghatározása az IOI-k alapján
    def find_optimal_gap(self):
        if len(self.iois) < 5: # túl kevés adat
            if self.last_optimal_gap < 0.1:
                self.optimal_gap = min(0.20, self.last_optimal_gap * 1.2)
                print(f"Kevés az adat a hisztogramhoz, ELŐZŐ min_gap = {self.last_optimal_gap:.3f}s lesz.")
            else:
                self.optimal_gap = 0.35
                print("Kevés az adat a hisztogramhoz, min_gap = 0.35s lesz.")
            self.last_optimal_gap = self.optimal_gap
            return self.optimal_gap
        
        fastest = np.percentile(self.iois, 50)
        if fastest < 0.1: # ha nagyon gyors hangok vannak
            self.dominant_interval = fastest
            self.optimal_gap = max(0.04, fastest * 0.6)
            print(f"Gyakori gyors hangok miatt min_gap = {self.optimal_gap:.3f}s lesz.")
            self.last_optimal_gap = self.optimal_gap
            return self.optimal_gap
        
        hist, bin_edges = np.histogram(self.iois, bins=30, range=(0.03, 1.0)) # hisztogram készítése
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2 # megjelenítéshez a közepe kell
        smooth_hist = gaussian_filter1d(hist, sigma=2) # hisztogram simítása

        valid_start_idx = np.searchsorted(bin_centers, 0.06) # kihagyjuk az elejét, mert az csak zaj
        valid_start_idx = 0 if valid_start_idx >= len(smooth_hist) else valid_start_idx

        if len(smooth_hist[valid_start_idx:]) > 0:
            relevant_max = np.max(smooth_hist[valid_start_idx:])
        else:
            relevant_max = np.max(smooth_hist)

        peaks, _ = find_peaks(smooth_hist, height=relevant_max*0.2, prominence=1) # csúcsok keresése a hisztogramon

        self.bin_edges = bin_edges
        self.hist = hist
        self.smooth_hist = smooth_hist
        self.peaks = peaks
        self.bin_centers = bin_centers

        # a legmagasabb csúcs kiválasztása, ami nagyobb mint 40ms
        if len(peaks) > 0:
            best_peak_time = None
            for p_idx in peaks:
                time_val = bin_centers[p_idx]
                if time_val > 0.04:
                    best_peak_time = time_val
                    break 
            
            if best_peak_time is not None:
                self.dominant_interval = best_peak_time
                self.optimal_gap = np.clip(best_peak_time * 0.6, 0.05, 0.35) # 50ms és 350ms közé szorítva
            else:
                print("Csak zajcsúcsok voltak, min_gap = 0.35s lesz.")
                self.optimal_gap = 0.35
        else:
            print("Nem találtam csúcsot, min_gap = 0.35s lesz.")
            self.optimal_gap = 0.35
        self.last_optimal_gap = self.optimal_gap
        return self.optimal_gap

    # BPM kiszámítása a domináns intervallum alapján
    def get_bpm(self):
        if self.dominant_interval <= 0:
            return 120
        
        bpm = 60.0 / self.dominant_interval
        if self.dominant_interval < 0.18:
            min_bpm = 100
            max_bpm = 220
        else:
            min_bpm = 60
            max_bpm = 160

        while bpm > max_bpm:
            bpm /= 2
        while bpm < min_bpm:
            bpm *= 2
        return int(round(bpm))

    