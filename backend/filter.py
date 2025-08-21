from scipy import signal

class BandpassFilter:
    def __init__(self, original_audio):
        self.original_audio = original_audio
    
    def bandpass_filter(self, original, fs, lowcut, highcut, order=5):
        nyq = fs*0.5
        low = lowcut/nyq
        high = highcut/nyq
        b, a = signal.butter(order, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, original)
        return filtered