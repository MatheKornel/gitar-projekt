import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

class OnsetHistogram:
    def __init__(self):
        self.onsets = None
        self.iois = []
        self.optimal_gap = 0.25
        self.bin_edges = None
        self.hist = None
        self.smooth_hist = None
        self.peaks = None
        self.bin_centers = None

    # IOI --> Inter-Onset Intervals kiszámítása --> szomszédos hangok távolsága
    def calculate_iois(self, onsets, min = 0.06, max = 1.0):
        self.onsets = np.array(onsets)
        if len(self.onsets) < 2:
            return []
        diffs = np.diff(self.onsets)
        self.iois = diffs[(diffs >= min) & (diffs <= max)]
        return self.iois
    
    # az optimális min_gap meghatározása az IOI-k alapján
    def find_optimal_gap(self):
        if len(self.iois) == 0:
            print("Nincs elég adat a hisztogramhoz.")
            return self.optimal_gap
        hist, bin_edges = np.histogram(self.iois, bins=60, range=(0.03, 1.0)) # hisztogram készítése
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2 # megjelenítéshez a közepe kell
        smooth_hist = gaussian_filter1d(hist, sigma=2) # hisztogram simítása

        valid_start_idx = np.searchsorted(bin_centers, 0.06)
        if valid_start_idx >= len(smooth_hist):
            valid_start_idx = 0
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

        if len(peaks) > 0:
            best_peak_time = None
            for p_idx in peaks:
                time_val = bin_centers[p_idx]
                if time_val > 0.04:
                    best_peak_time = time_val
                    break 
            
            if best_peak_time is not None:
                self.optimal_gap = np.clip(best_peak_time * 0.85, 0.05, 0.25)
            else:
                print("Csak zajcsúcsok voltak.")
                self.optimal_gap = 0.25
        else:
            print("Nem találtam csúcsot.")
            self.optimal_gap = 0.25

        return self.optimal_gap
    
    def show_histogram(self):
        
        plt.figure(figsize=(10, 6))
        
        plt.hist(self.iois, bins=50, range=(0.06, 1.0), alpha=0.5, color='gray', label='Nyers IOI eloszlás') # nyers hisztogram
        
        plt.plot(self.bin_centers, self.smooth_hist, color='blue', linewidth=2, label='Simított eloszlás') # simított
        
        if len(self.peaks) > 0:
            plt.plot(self.bin_centers[self.peaks], self.hist[self.peaks], "x", color='red', markersize=10, label='Csúcsok') # megtalált csúcsok megjelölése
            first_peak = self.peaks[0]
            plt.axvline(self.bin_centers[first_peak], color='green', linestyle='--', label=f'Választott: {self.bin_centers[first_peak]:.2f}s')

        plt.title(f"IOI - Javasolt min_gap: {self.optimal_gap:.3f}s")
        plt.xlabel("Időkülönbség (sec)")
        plt.ylabel("Gyakoriság (db)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

    