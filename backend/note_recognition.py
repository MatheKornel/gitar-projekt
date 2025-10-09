import librosa as lb
import numpy as np

from onset_offset_detection import OnsetOffsetDetection

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered

    def note_rec(self, max_harmonics):
        nfft = 4096
        fs = 44100
        guitar_notes = [
            82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81,
            138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65,
            220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63,
            349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25,
            554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99, 830.61,
            880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51]
        
        onset = OnsetOffsetDetection(self.filtered)

        #STFT
        D = lb.stft(self.filtered, n_fft=nfft, hop_length=512, window="blackman", center=False)
        freqs = lb.fft_frequencies(sr=44100, n_fft=nfft)
        magnitude = np.abs(D)
        dominant_bins = magnitude.argmax(axis=0)
        dominant_freqs = freqs[dominant_bins]

        #HS
        all_f0 = []
        for i in range(len(dominant_freqs)):
            f0 = dominant_freqs[i]
            tau = fs/f0
            m = 0
            harmonics = []
            s = 1.0
            for j in range(max_harmonics):
                m += 1
                freq = m*(fs/tau)
                amp = 0.0
                for k in range(len(freqs)):
                    if abs(freq - freqs[k]) <= 4.5:
                        amp += float(magnitude[k, i])
                salience = amp*s
                s = s/4
                salience = 1-np.exp(-salience)
                harmonics.append((freq, amp, salience))
            max_salience = max(harmonics, key=lambda x: x[2])
            f0_candidate = max_salience[0]
        
        #Ha felezem a frekvenciát, van-e számottevő salience értéke, tehát lehet-e alaphang
            def near_salience(freq, tol = 4.5):
                for f, m, s in harmonics:
                    if abs(f - freq) <= tol and s > 0.4:
                        return True
                return False

            temp = f0_candidate
            best_f0 = f0_candidate
            while temp > 75:
                temp = temp/2
                if near_salience(temp):
                    best_f0 = temp
                else:
                    break
            all_f0.append(best_f0)

        def select_notes(f0_list, tol, min_frames):
            notes = []
            current_note = []
            for f in f0_list:
                if not current_note:
                    current_note = [f]
                elif abs(f - np.mean(current_note)) <= tol:
                    current_note.append(f)
                else:
                    if len(current_note) >= min_frames:
                        avg_note=np.mean(current_note)
                        if not notes or abs(avg_note - notes[-1]) > tol:
                            notes.append(avg_note)
                    current_note = [f]
            if current_note and len(current_note) >= min_frames:
                avg_note=np.mean(current_note)
                if not notes or abs(avg_note - notes[-1]) > tol:
                    notes.append(avg_note)
            return notes
                
        #Bináris keresés a guitar_notes-ban
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
                

        all_notes = select_notes(all_f0, 4.5, 50)
        
        final_notes = []
        for f in all_notes:
            if serach_in_notes(guitar_notes, f, 4.5):
                final_notes.append(f)
            else:
                temp = f
                while temp > 75:
                    temp = temp / 2
                    if serach_in_notes(guitar_notes, temp, 4.5):
                        final_notes.append(temp)
                        break

        onsets = onset.onset_detect()

        formatted_notes = [f"{float(f):.2f} Hz" for f in final_notes]
        print("All f0 frequencies:", ", ".join(formatted_notes))



        
        
