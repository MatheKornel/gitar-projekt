from scipy import signal

class BandpassFilter:
    def __init__(self, original_audio):
        self.original_audio = original_audio # eredeti audio jel
    
    def bandpass_filter(self, original, fs, lowcut, highcut, order=5):
        nyq = fs*0.5
        low = lowcut/nyq
        high = highcut/nyq
        # másodrendű szakaszok (SOS): mély hangolásoknál (B és lejjebb) a (b, a) alak numerikusan instabil, inf/NaN lesz a kimenet
        sos = signal.butter(order, [low, high], btype='band', output='sos')
        filtered = signal.sosfiltfilt(sos, original)
        return filtered