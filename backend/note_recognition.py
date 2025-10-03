import librosa as lb
import numpy as np
import statistics

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered

    def note_rec(self, max_harmonics):
        nfft = 2048
        fs = 44100

        #STFT
        D = lb.stft(self.filtered, n_fft=nfft, hop_length=512, window="hamming", center=False)
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
                    if (freqs[k] >= freq-4) and (freqs[k] <= freq+4):
                        amp += float(magnitude[k, i])
                salience = amp*s
                s = s/4
                salience = 1-np.exp(-salience)
                harmonics.append((round(freq, 4), round(amp, 4), round(salience, 4)))
                #print(harmonics)
            max_salience = max(harmonics, key=lambda x: x[2])
            f0_candidate = max_salience[0]
        
        #Ha felezem a frekvenciát, van-e számottevő salience értéke, tehát lehet-e alaphang
            def near_salience(freq, tol = 4):
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
            #print(f"{best_f0}")
            all_f0.append(round(best_f0, 2))

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
                        avg_note=round(np.mean(current_note), 2)
                        if not notes or abs(avg_note - notes[-1]) > tol:
                            notes.append(avg_note)
                    current_note = [f]
            if current_note and len(current_note) >= min_frames:
                avg_note=round(np.mean(current_note), 2)
                if not notes or abs(avg_note - notes[-1]) > tol:
                    notes.append(avg_note)
            return notes
                
        
        all_notes = select_notes(all_f0, 2, 30)

        print(f"All f0 frequencies: {all_notes}")



        
        
