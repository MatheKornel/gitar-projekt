import librosa as lb

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered
    
    def note_rec(self):
        D = lb.stft(self.filtered, n_fft=2048, hop_length=512, window="hamming", center=False)
        print(D)