import librosa as lb
import numpy as np

from onset_offset_detection import OnsetOffsetDetection

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered
        self.fs = 44100

    # egyetlen frame-re kiszámoljuk az alaphangot
    def get_f0_from_frame(self, i, dominant_freqs, magnitude, freqs, fs, max_harmonics, guitar_notes):
        
        # Keresés a guitar_notes-ban
        def serach_in_notes(notes, value, tol):
            left = 0
            right = len(notes) - 1
            while left <= right:
                center = (left + right) // 2
                if abs(notes[center] - value) <= tol:
                    return True
                elif notes[center] < value:
                    left = center + 1
                else:
                    right = center - 1
            return False
        
        # HS
        f0 = dominant_freqs[i]
        if f0 == 0:
            return None
        tau = fs / f0
        harmonics = []
        s = 1.0
        for j in range(max_harmonics):
            m = j + 1
            freq = m * (fs / tau)
            amp = 0.0
            nearby_bins = np.where(np.abs(freqs - freq) <= 4.5)[0]
            if nearby_bins.size > 0:
                amp = np.sum(magnitude[nearby_bins, i])
            
            salience = amp * s
            s /= 4
            salience = 1 - np.exp(-salience)
            harmonics.append((freq, amp, salience))
        
        if not harmonics:
            return None
        
        max_salience = max(harmonics, key=lambda x: x[2])
        f0_candidate = max_salience[0]
        f0_candidate_amp = max_salience[1]

        # ha felezem a frekvenciát, van-e számottevő salience értéke, tehát lehet-e alaphang
        def near_salience(freq, tol = 4.5, amp_treshold = 0.1):
            nearby_bins = np.where(np.abs(freqs - freq) <= tol)[0] # megkeressük a frekvenciához közeli bin-eket
            if nearby_bins.size == 0:
                return False
            amp = np.sum(magnitude[nearby_bins, i]) # kiolvassuk az amplitúdót
            if amp > (f0_candidate_amp * amp_treshold) and amp > 0.01:
                return True
            return False

        temp = f0_candidate
        best_f0 = f0_candidate
        while temp > 75:
            temp = temp / 2
            if near_salience(temp):
                best_f0 = temp
            else:
                break
            
        if serach_in_notes(guitar_notes, best_f0, 4.5): #először megróbáljuk visszaadni ha benne van a guitar_notes-ban
            return best_f0
        else:
            if serach_in_notes(guitar_notes, f0_candidate, 4.5): #ha nem, akkor az eredeti felezés nélküli f0_candidate-et
                return f0_candidate
        return None


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
        dominant_bins = magnitude.argmax(axis=0)
        dominant_freqs = freqs[dominant_bins]

        # frame-ekhez tartozó időpontok
        times = lb.frames_to_time(np.arange(D.shape[1]), sr=fs, hop_length=hop_length)
        
        final_notes = []
        for onset in onsets:
            onset_frame_idx = np.argmin(np.abs(times - onset)) # onset-hez tartozó frame indexe
            start_frame = onset_frame_idx + 2
            end_frame = onset_frame_idx + 10 # veszünk egy 8 fram-es ablakot az onset után, elkerülhetjük a pengetés kezdeti zaját

            if end_frame >= len(dominant_freqs):
                end_frame = len(dominant_freqs) - 1
            if start_frame >= end_frame:
                continue

            f0_candidates = []
            for i in range(start_frame, end_frame):
                f0 = self.get_f0_from_frame(i, dominant_freqs, magnitude, freqs, fs, max_harmonics, guitar_notes)
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


        
        
