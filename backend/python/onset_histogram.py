import numpy as np
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

# Tempóbecslés a hangkezdetekből: az egymást követő onsetek közötti időkből (IOI, Inter-Onset Interval)
# simított hisztogramot készítünk, és a legrövidebb gyakori időközt tekintjük egy ütés hosszának.

DEFAULT_BPM = 120            # ha a becslés nem lehetséges
MIN_IOI = 0.05               # ennél rövidebb időköz zaj (mp)
MAX_IOI = 1.0                # ennél hosszabb időköz szünet, nem a ritmus része (mp)
MIN_IOI_COUNT = 5            # ennél kevesebb időközből nem becslünk
FAST_PERCENTILE = 60         # gyors daloknál az időközök ennyiedik percentilise adja az ütés hosszát
FAST_IOI_LIMIT = 0.18        # ha ez a percentilis ennél rövidebb (mp), a dal gyors, nem kell hisztogram
HIST_BINS = 30               # a hisztogram sávjainak száma
HIST_RANGE = (0.03, 1.0)     # a hisztogram tartománya (mp)
HIST_SMOOTHING = 2           # a Gauss-simítás szórása (sávban)
NOISE_LIMIT = 0.06           # a hisztogram eleje (ennél rövidebb időközök) csak zaj, a csúcsmagasság küszöbéhez nem számít
PEAK_HEIGHT_RATIO = 0.2      # csúcsnak csak a legmagasabb csúcs ennyiszerese feletti számít
PEAK_PROMINENCE = 1          # a csúcs ennyivel emelkedjen ki a környezetéből
FAST_BPM_RANGE = (100, 220)  # gyors daloknál ebbe a tartományba igazítjuk a BPM-et
NORMAL_BPM_RANGE = (60, 160) # egyébként ebbe


# az egymást követő onsetek közötti idők, csak a MIN_IOI és MAX_IOI közöttiek
def inter_onset_intervals(onsets):
    onsets = np.array(onsets)
    if len(onsets) < 2:
        return np.array([])
    diffs = np.diff(onsets)
    return diffs[(diffs >= MIN_IOI) & (diffs <= MAX_IOI)]


# egy ütés hossza (mp) az időközökből, vagy None, ha nem becsülhető
def dominant_interval(iois):
    if len(iois) < MIN_IOI_COUNT: # túl kevés adat
        return None

    # gyors daloknál az időközök többsége rövid: ilyenkor közvetlenül a percentilist használjuk
    fastest = np.percentile(iois, FAST_PERCENTILE)
    if fastest < FAST_IOI_LIMIT:
        return fastest

    # simított hisztogram, és annak első (legrövidebb időközhöz tartozó) elég magas csúcsa
    hist, bin_edges = np.histogram(iois, bins=HIST_BINS, range=HIST_RANGE)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    smooth_hist = gaussian_filter1d(hist, sigma=HIST_SMOOTHING)

    valid_start_idx = np.searchsorted(bin_centers, NOISE_LIMIT) # a csúcsmagasság küszöbét a zaj nélküli részből számoljuk
    relevant_max = np.max(smooth_hist[valid_start_idx:])

    peaks, _ = find_peaks(smooth_hist, height=relevant_max * PEAK_HEIGHT_RATIO, prominence=PEAK_PROMINENCE)
    if len(peaks) == 0:
        return None
    return bin_centers[peaks[0]]


# a BPM becslése az onsetekből; a kapott értéket felezéssel / duplázással életszerű tartományba igazítja
def estimate_bpm(onsets):
    interval = dominant_interval(inter_onset_intervals(onsets))
    if interval is None or interval <= 0:
        print(f"A tempó nem becsülhető (kevés onset vagy nincs csúcs a hisztogramon), alapértelmezett: {DEFAULT_BPM} BPM.")
        return DEFAULT_BPM

    if interval < FAST_IOI_LIMIT:
        min_bpm, max_bpm = FAST_BPM_RANGE
    else:
        min_bpm, max_bpm = NORMAL_BPM_RANGE

    bpm = 60.0 / interval
    while bpm > max_bpm:
        bpm /= 2
    while bpm < min_bpm:
        bpm *= 2
    return int(round(bpm))
