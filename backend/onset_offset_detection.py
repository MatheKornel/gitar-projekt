from stockwell import st
import numpy as np

class OnsetOffsetDetection:
    def __init__(self, filtered):
        self.filtered = filtered

    def onset_detect(self):
        S = st.st(data=self.filtered, lo=75, hi=1350, gamma=2, win_type='gauss')
        num_freqs, num_times = S.shape
        freqs = np.linspace(75, 1350, num_freqs)
        times = np.arange(num_times) * 0.01

        amp = np.sum(np.abs(S), axis=0)
        amp_diff = np.diff(amp)
        onset_times = np.where(amp_diff > np.percentile(amp_diff, 99))[0]
        onsets = times[onset_times]
        return onsets