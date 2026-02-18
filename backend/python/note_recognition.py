import librosa as lb
import numpy as np
import os

from onset_detect import OnsetDetect
from note_event import NoteEvent
from onset_histogram import OnsetHistogram

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
    
    # onset detektálás ablakonként, hisztogram alapján változó min_gap paraméterrel
    def onsets_in_window(self, onset, envelope, histogram, windows_size = 1.8, hop_size = 0.2):
        onsets = []
        duration = len(envelope) / onset.fs # jel hossza másodpercben
        starts = np.arange(0, duration, hop_size) # ablakok kezdőpontjai

        for step_start in starts:
            step_end = step_start + hop_size
            window_start = max(0, step_start + hop_size / 2 - windows_size / 2) # ablak kezdete
            window_end = min(duration, window_start + windows_size) # ablak vége

            envelope_cut_start = int(window_start * onset.fs) # kivágás kezdete
            envelope_cut_end = int(window_end * onset.fs) # kivágás vége
            envelope_window = envelope[envelope_cut_start:envelope_cut_end] # kivágott envelope ablak

            temp_onsets = onset.get_onsets(envelope_window,min_gap=0.03, prominence=0.08) # érzékenyebb onset detektálás az ablakon belül
            histogram.calculate_iois(temp_onsets, min=0.05) # kiszámoljuk az IOI-kat az ablakon belül
            optimal_gap = histogram.find_optimal_gap() # meghatározzuk az optimális min_gap-et

            # prominence beállítása az optimal_gap alapján
            if optimal_gap < 0.15:
                current_prominence = 0.02
            elif optimal_gap < 0.25:
                current_prominence = 0.1
            else:
                current_prominence = 0.25

            relative_onsets = onset.get_onsets(envelope_window, min_gap=optimal_gap, prominence=current_prominence) # végleges onset detektálás az ablakon belül már az optimal_gap-pel
            absolute_onsets = relative_onsets + window_start # abszolút időpontokra váltás
            final_onsets = [t for t in absolute_onsets if step_start <= t < step_end] # csak az aktuális lépésbe eső onset-ek megtartása
            onsets.extend(final_onsets)
        
        onsets = np.unique(onsets)
        onsets.sort()
        histogram.last_optimal_gap = 0.35 # alaphelyzetbe állítás
        return onsets
    
    def save_note_to_txt(self, notes, file_name="notes.txt"):
        path = "D:\\Sulis dolgok\\gitar_projekt\\backend\\cpp\\pso_fingering_optimization\\"
        try:
            with open(os.path.join(path, file_name), "w") as f:
                f.write(f"{len(notes)}\n")
                for note in notes:
                    note_name = note.note_name.replace('\u266f', '#')
                    f.write(f"{int(note.midi_note)} {note.onset:.4f} {note.duration:.4f} {note_name}\n")
            print(f"Hangok sikeresen elmentve: {file_name}")
        except Exception as e:
            print(f"Sikertelen mentés: {e}")



    def note_rec(self, max_harmonics, histogram):
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
        
        # ONSET DETEKTÁLÁS
        onset = OnsetDetect(self.filtered, fs=self.fs)
        envelope = onset.make_envelope() # teljes jel envelope-ja (időigényes, ezért csak egyszer számoljuk ki)
        onsets = self.onsets_in_window(onset, envelope, histogram, 1.8, 0.2) # ablakos onset detektálás hisztogram alapján

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
                last_f = notes_with_offsets[-1].freq

                time_diff = onset - last_t
                freq_diff = abs(recognized_note - last_f)

                if time_diff < 0.05:
                    is_duplicate = True
                else:
                    resonance_treshold = 0.08 if time_diff < 0.15 else 0.25 # rezonancia küszöb idő alapján
                    if freq_diff < 2.5 and time_diff < resonance_treshold: # ha nagyon közel van az előző hanghoz időben és frekvenciában is, akkor rezonancia lehet
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

            salience_treshold = peak_salience * 0.25 # a küszöb legyen a csúcs valahány százaléka

            offset_time = times[peak_frame] # elkezdjük követni a lecsengést
            for j in range(peak_frame + 1, magnitude.shape[1]):
                current_time = times[j]
                current_salience = self.get_f0_salience(f0, j, magnitude, freqs, fs, max_harmonics)
                if current_salience < salience_treshold:
                    offset_time = current_time
                    break
                offset_time = current_time

            event = NoteEvent(onset, offset_time, f0)
            notes_with_offsets.append(event) # minden egyes hangról egy NoteEvent objektumot tárolunk el

        for note in notes_with_offsets:
            print(f"Felismert hang: {note.note_name} - {note.freq:.2f} Hz, onset: {note.onset:.2f} s, offset: {note.offset:.2f} s")
        
        if notes_with_offsets:
            self.save_note_to_txt(notes_with_offsets)
        else:
            print("Nincsenek hangok a fájlba mentéshez!")

        return notes_with_offsets, envelope



        
        
