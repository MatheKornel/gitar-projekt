import librosa as lb
import numpy as np
import os

from onset_detect import OnsetDetect
from note_event import NoteEvent
from guitar_note_freqs import GuitarNoteFreqs

class ShortTimeFT:
    def __init__(self, filtered):
        self.filtered = filtered # szűrt audio jel
        self.fs = 44100 # mintavételi frekvencia

    # egy adott frekvenciára kiszámolja a salience-t egy adott frame-ben
    def get_f0_salience(self, f0, i, magnitude, freqs, fs, max_harmonics):
        salience = 0.0

        for m in range(1, max_harmonics + 1):
            freq = f0 * m
            if freq > fs / 2:
                break
            
            tol_hz = max(freq * 0.03, 4.5)  # dinamikusabb tolerancia a magasabb hangok miatt
            nearby_bins = np.where(np.abs(freqs - freq) <= tol_hz)[0]
            amp = 0.0
            if nearby_bins.size > 0:
                amp = np.sum(magnitude[nearby_bins, i])
            
            salience += amp
        
        return salience

    # egyetlen frame-re kiszámoljuk az alaphangot, lentről felfele építkezve
    # minden egyes létező hangra kiszámolok egy pontszámot (salience) és a legjobbat választom
    def get_f0_from_frame(self, i, magnitude, freqs, fs, max_harmonics, guitar_notes):
        
        f0_candidate_salience = []

        # végigmegyek az összes gitárhangon
        for f0_candidate in guitar_notes:
            
            # a túl mélyeket és túl magasakat kihagyom
            if f0_candidate < 75:
                continue

            salience = 0.0

            # felharmonikusok összeadása
            for m in range(1, max_harmonics + 1):
                freq = f0_candidate * m
                if freq > fs / 2:
                    break
                
                tol_hz = max(freq * 0.03, 4.5)
                nearby_bins = np.where(np.abs(freqs - freq) <= tol_hz)[0]
                amp = 0.0
                if nearby_bins.size > 0:
                    amp = np.sum(magnitude[nearby_bins, i])
                
                if m == 1:
                    salience += amp * 1.0
                else:
                    salience += amp * 0.8 # felharmonikust csak egy kicsit büntetek
            
            if salience > 0.01: # küszöb a zaj ellen
                f0_candidate_salience.append((f0_candidate, salience))

        # kiválasztom a legjobbat
        if not f0_candidate_salience:
            return None

        best_candidate, _ = max(f0_candidate_salience, key=lambda x: x[1])
        
        return best_candidate
    

    def note_rec(self, max_harmonics, histogram, tuning="E"):
        nfft = 4096
        fs = 44100
        hop_length = 512

        # gitár hangok frekvenciái
        guitar_note_freqs = GuitarNoteFreqs()
        guitar_notes = guitar_note_freqs.select_tuning(tuning)
        
        # ONSET DETEKTÁLÁS
        onset = OnsetDetect(self.filtered, fs=self.fs)
        onsets = onset.get_onsets(min_gap=0.05)

        # hisztogram most csak a bpm becsléshez
        histogram.calculate_iois(onsets)
        histogram.find_optimal_gap()

        print(f"Onsetek ({len(onsets)} db): {[round(t, 2) for t in onsets]}")

        notes_with_offsets = []
        freqs = lb.fft_frequencies(sr=fs, n_fft=nfft)
        
        for i in range(len(onsets)):
            onset = onsets[i]

            start_sample = int(onset * fs)
            slice_end_time = onset + 5.0 # alapértelmezetten 5 mp után vége
            
            next_onset = onsets[i + 1] if i < len(onsets) - 1 else (onset + 5.0)
            slice_end_time = min(onset + 5.0, next_onset + 0.1) # de amúgy a szelet vége legyen a következő onset közelében

            end_sample = int(slice_end_time * fs)
            
            end_sample = len(self.filtered) if end_sample > len(self.filtered) else end_sample

            if (end_sample - start_sample) < (fs * 0.1): # ha túl rövid a szelet, kihagyom
                continue

            audio_slice = self.filtered[start_sample:end_sample]

            # STFT számolása csak a szeletre
            D = lb.stft(audio_slice, n_fft=nfft, hop_length=hop_length, window="blackman", center=False)
            magnitude = np.abs(D)
            # frame-ekhez tartozó időpontok
            times = lb.frames_to_time(np.arange(D.shape[1]), sr=fs, hop_length=hop_length) + onset # az onset-től induló időket kell tartalmaznia
            
            onset_frame_idx = np.argmin(np.abs(times - onset))
            start_frame = onset_frame_idx + 1
            end_frame = min(onset_frame_idx + 10, magnitude.shape[1] - 1) # veszünk egy 8 frame-es ablakot az onset után, elkerülhetjük a pengetés kezdeti zaját

            if start_frame >= end_frame:
                continue

            f0_candidates = []
            for j in range(start_frame, end_frame):
                f0 = self.get_f0_from_frame(j, magnitude, freqs, fs, max_harmonics, guitar_notes) # alaphang meghatározása az adott frame-ben
                if f0 is not None:
                    f0_candidates.append(f0)

            if not f0_candidates:
                print(f"Az onset (t={onset:.2f}s) körül nincs hang")
                continue

            stable_f0 = np.median(f0_candidates) # legstabilabb f0 az ablakból
            note_idx = np.argmin(np.abs(guitar_notes - stable_f0))
            recognized_note = guitar_notes[note_idx]

            # rezonancia szűrés
            is_duplicate = False
            if notes_with_offsets:
                last_t = notes_with_offsets[-1].onset
                time_diff = onset - last_t

                if time_diff < 0.05:
                    is_duplicate = True

            if is_duplicate:
                continue
        
            # OFFSET DETEKTÁLÁS

            f0 = recognized_note
            peak_salience = 0.0
            peak_frame = start_frame

            for j in range(start_frame, end_frame):
                current_salience = self.get_f0_salience(f0, j, magnitude, freqs, fs, max_harmonics) # salience számolás az adott frame-ben
                if current_salience > peak_salience:
                    peak_salience = current_salience
                    peak_frame = j # ez most a szeleten belüli frame index

            if peak_salience < 0.01:
                notes_with_offsets.append((onset, f0, onset + 0.1)) # ha a hang túl rövid adok neki egy fix hosszt
                continue

            salience_treshold = peak_salience * 0.1 # a küszöb legyen a csúcs valahány százaléka

            offset_time = times[peak_frame] # elkezdjük követni a lecsengést

            next_onset_time = onsets[i + 1] if i < len(onsets) - 1 else (onset + 5.0) # ha nagyon összecsúszna az onset és offset, akkor a következő onset-ig követjük csak a lecsengést

            for j in range(peak_frame + 1, magnitude.shape[1]):
                current_time = times[j]

                if current_time >= next_onset_time:
                    offset_time = next_onset_time - 0.01
                    break

                current_salience = self.get_f0_salience(f0, j, magnitude, freqs, fs, max_harmonics)

                if current_salience < salience_treshold:
                    offset_time = current_time
                    break
                
                offset_time = current_time

            event = NoteEvent(onset, offset_time, f0)
            notes_with_offsets.append(event) # minden egyes hangról egy NoteEvent objektumot tárolunk el

        for note in notes_with_offsets:
            print(f"Felismert hang: {note.note_name} - {note.freq:.2f} Hz, onset: {note.onset:.2f} s, offset: {note.offset:.2f} s")
        print(f"Felismert hangok száma: {len(notes_with_offsets)}")

        return notes_with_offsets



        
        
