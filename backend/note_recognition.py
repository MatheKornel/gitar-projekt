import librosa as lb
import numpy as np

from onset_offset_detection import OnsetOffsetDetection

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered
        self.fs = 44100

    # egyetlen frame-re kiszámoljuk az alaphangot, lentről felfele építkezve
    # minden egyes létező hangra kiszámolok egy pontszámot (salience) és a legjobbat választom
    def get_f0_from_frame(self, i, magnitude, freqs, fs, max_harmonics, guitar_notes):
        
        f0_candidate_salience = []

        # végigmegyek az összes gitárhangon
        for f0_candidate in guitar_notes:
            
            # a túl mélyeket és túl magasakat kihagyom
            if f0_candidate < 75 or f0_candidate > fs / (2 * max_harmonics):
                continue

            salience = 0.0

            # felharmonikusok összeadása
            for m in range(1, max_harmonics + 1):
                freq = f0_candidate * m
                if freq > fs / 2:
                    break
                
                nearby_bins = np.where(np.abs(freqs - freq) <= 4.5)[0]
                amp = 0.0
                if nearby_bins.size > 0:
                    amp = np.sum(magnitude[nearby_bins, i])
                
                salience += amp
            
            if salience > 0.01: # küszöb a zaj ellen
                f0_candidate_salience.append((f0_candidate, salience))

        # kiválasztom a legjobbat
        if not f0_candidate_salience:
            return None

        best_candidate, best_salience = max(f0_candidate_salience, key=lambda x: x[1])
        
        return best_candidate


    def note_rec(self, max_harmonics):
        nfft = 4096
        fs = 44100
        hop_length = 512

        # gitár hangok frekvenciái
        guitar_notes = [
            82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81,
            138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65,
            220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63,
            349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25,
            554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99, 830.61,
            880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51]
        
        # onset detektálás
        onset = OnsetOffsetDetection(self.filtered, fs=self.fs)
        onsets = onset.onset_detect(min_gap=0.3)

        print(f"Onsetek ({len(onsets)} db): {[round(t, 2) for t in onsets]}")

        #STFT
        D = lb.stft(self.filtered, n_fft=nfft, hop_length=hop_length, window="blackman", center=False)
        freqs = lb.fft_frequencies(sr=fs, n_fft=nfft)
        magnitude = np.abs(D)

        # frame-ekhez tartozó időpontok
        times = lb.frames_to_time(np.arange(D.shape[1]), sr=fs, hop_length=hop_length)
        
        final_notes = []
        for onset in onsets:
            onset_frame_idx = np.argmin(np.abs(times - onset)) # onset-hez tartozó frame indexe
            start_frame = onset_frame_idx + 2
            end_frame = onset_frame_idx + 10 # veszünk egy 8 fram-es ablakot az onset után, elkerülhetjük a pengetés kezdeti zaját

            if end_frame >= magnitude.shape[1]:
                end_frame = magnitude.shape[1] - 1
            if start_frame >= end_frame:
                continue

            f0_candidates = []
            for i in range(start_frame, end_frame):
                f0 = self.get_f0_from_frame(i, magnitude, freqs, fs, max_harmonics, guitar_notes)
                if f0 is not None:
                    f0_candidates.append(f0)

            if not f0_candidates:
                print(f"Az onset (t={onset:.2f}s) körül nincs hang")
                continue

            stable_f0 = np.median(f0_candidates) # legstabilabb f0 az ablakból
            note_idx = np.argmin(np.abs(guitar_notes - stable_f0))
            recognized_note = guitar_notes[note_idx]
            final_notes.append((onset, recognized_note))

        if not final_notes:
            print("Nincs felismert hang a hanganyagban.")
        else:
            for t, f in final_notes:
                print(f"Felismert hang: {f:.2f} Hz, időpont: {t:.2f} s")
        return final_notes


        
        
