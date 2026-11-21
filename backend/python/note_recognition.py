import librosa as lb
import numpy as np

from onset_detect import OnsetDetect
from note_event import NoteEvent
from guitar_note_freqs import GuitarNoteFreqs

class ShortTimeFT:
    NFFT = 4096                   # STFT ablakméret
    HOP_LENGTH = 512              # STFT ablaklépés
    ZERO_PAD_FACTOR = 4           # a hangmagasság becsléshez ennyiszeresére zero-paddelt spektrum
    MAX_NOTE_LENGTH = 5.0         # egy hang legfeljebb ennyi mp-ig tarthat
    SLICE_OVERLAP = 0.1           # a szelet ennyivel nyúlik túl a következő onseten (mp)
    MIN_SLICE_LENGTH = 0.1        # ennél rövidebb szeletet nem vizsgálunk (mp)
    PITCH_FRAMES_END = 10         # a hangmagasság becsléshez az onset utáni 1-9. frame (a pengetés zaját kihagyjuk)
    HARMONIC_WEIGHT = 0.8         # a felharmonikusok súlya az alaphanghoz képest
    MIN_SALIENCE = 0.01           # küszöb a zaj ellen
    DUPLICATE_GAP = 0.05          # az előző hanghoz ennyi mp-nél közelebbi onset rezonancia, nem új hang
    SHORT_NOTE_LENGTH = 0.1       # ha a hang nem mérhető, ilyen fix hosszt kap (mp)
    OFFSET_THRESHOLD_RATIO = 0.1  # a hang véget ér, ha a salience a csúcs ennyiszerese alá esik
    OFFSET_MARGIN = 0.01          # a következő onset előtt ennyivel ér véget a hang (mp)

    def __init__(self, filtered, fs=44100):
        self.filtered = filtered # szűrt audio jel
        self.fs = fs # mintavételi frekvencia (a betöltött hangfájlból származik)
        self.onsets = [] # a note_rec által megtalált onsetek (a tempóbecsléshez)

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

    # egy felharmonikus amplitúdója: a frekvencia körüli ±25 centes sáv legnagyobb értéke a zero-paddelt spektrumban
    # a sáv centben (relatívan) van megadva, így nem függ attól, hogy a hang hova esik a bin-rácson --> minden hangolásban ugyanúgy mér
    def get_harmonic_amp(self, spectrum, freq, bin_hz):
        low_bin = int(np.ceil(freq * 2 ** (-25 / 1200) / bin_hz))
        high_bin = int(np.floor(freq * 2 ** (25 / 1200) / bin_hz))
        if high_bin < low_bin: # ha egy bin sem esik a sávba, a legközelebbit vesszük
            low_bin = high_bin = int(round(freq / bin_hz))
        return np.max(spectrum[low_bin:high_bin + 1])

    # egyetlen frame-re kiszámoljuk az alaphangot, lentről felfele építkezve
    # minden egyes létező hangra kiszámolok egy pontszámot (salience) és a legjobbat választom
    def get_f0_from_frame(self, spectrum, bin_hz, fs, max_harmonics, guitar_notes):
        best_candidate = None
        best_salience = 0.0

        # végigmegyek az összes gitárhangon
        for f0_candidate in guitar_notes:
            salience = 0.0

            # felharmonikusok összeadása
            for m in range(1, max_harmonics + 1):
                freq = f0_candidate * m
                if freq > fs / 2:
                    break

                amp = self.get_harmonic_amp(spectrum, freq, bin_hz)

                if m == 1:
                    salience += amp * 1.0
                else:
                    salience += amp * self.HARMONIC_WEIGHT # felharmonikust csak egy kicsit büntetek

            # a legjobb jelölt (egyenlő pontszámnál az elsőt, azaz a mélyebbet tartjuk meg)
            if salience > self.MIN_SALIENCE and (best_candidate is None or salience > best_salience):
                best_candidate = f0_candidate
                best_salience = salience

        return best_candidate

    # a hanghoz tartozó szelet: az onsettől legfeljebb MAX_NOTE_LENGTH mp-ig, de csak kicsivel a következő onset utánig
    # None, ha a szelet túl rövid a vizsgálathoz
    def _onset_slice(self, onset, next_onset):
        start_sample = int(onset * self.fs)
        slice_end_time = min(onset + self.MAX_NOTE_LENGTH, next_onset + self.SLICE_OVERLAP)
        end_sample = min(int(slice_end_time * self.fs), len(self.filtered))

        if (end_sample - start_sample) < (self.fs * self.MIN_SLICE_LENGTH):
            return None
        return self.filtered[start_sample:end_sample]

    # a szelet STFT-je (az offset kereséshez), a frame-ek időpontjai és a hangmagasság becslés frame-tartománya
    # None, ha a szeletben nincs elég frame
    def _slice_frames(self, audio_slice, onset):
        D = lb.stft(audio_slice, n_fft=self.NFFT, hop_length=self.HOP_LENGTH, window="blackman", center=False)
        magnitude = np.abs(D)
        # frame-ekhez tartozó időpontok, az onset-től indulva
        times = lb.frames_to_time(np.arange(D.shape[1]), sr=self.fs, hop_length=self.HOP_LENGTH) + onset

        onset_frame_idx = np.argmin(np.abs(times - onset))
        start_frame = onset_frame_idx + 1
        end_frame = min(onset_frame_idx + self.PITCH_FRAMES_END, magnitude.shape[1] - 1)

        if start_frame >= end_frame:
            return None
        return magnitude, times, start_frame, end_frame

    # hangmagasság becslés: frame-enként a legjobb alaphang a zero-paddelt spektrumból, ezek mediánjához legközelebbi gitárhang
    # None, ha egyik frame-ben sincs hang
    def _estimate_pitch(self, audio_slice, start_frame, end_frame, max_harmonics, guitar_notes, guitar_notes_arr):
        nfft_padded = self.NFFT * self.ZERO_PAD_FACTOR
        bin_hz = self.fs / nfft_padded
        window = lb.filters.get_window("blackman", self.NFFT, fftbins=True) # ugyanaz az ablak, mint az lb.stft-ben

        f0_candidates = []
        for j in range(start_frame, end_frame):
            frame = audio_slice[j * self.HOP_LENGTH:j * self.HOP_LENGTH + self.NFFT] * window # ugyanaz a frame, mint az STFT j. oszlopa
            spectrum = np.abs(np.fft.rfft(frame, n=nfft_padded))
            f0 = self.get_f0_from_frame(spectrum, bin_hz, self.fs, max_harmonics, guitar_notes) # alaphang meghatározása az adott frame-ben
            if f0 is not None:
                f0_candidates.append(f0)

        if not f0_candidates:
            return None

        stable_f0 = np.median(f0_candidates) # legstabilabb f0 az ablakból
        note_idx = int(np.argmin(np.abs(guitar_notes_arr - stable_f0)))
        return guitar_notes[note_idx]

    # offset keresés: a salience csúcsától addig követjük a lecsengést, amíg a csúcs adott része alá nem esik,
    # de legfeljebb a következő onsetig
    def _find_offset(self, f0, onset, next_onset, magnitude, freqs, times, start_frame, end_frame, max_harmonics):
        peak_salience = 0.0
        peak_frame = start_frame

        for j in range(start_frame, end_frame):
            current_salience = self.get_f0_salience(f0, j, magnitude, freqs, self.fs, max_harmonics) # salience számolás az adott frame-ben
            if current_salience > peak_salience:
                peak_salience = current_salience
                peak_frame = j # ez most a szeleten belüli frame index

        if peak_salience < self.MIN_SALIENCE:
            return onset + self.SHORT_NOTE_LENGTH # ha a hang túl rövid, adok neki egy fix hosszt

        salience_treshold = peak_salience * self.OFFSET_THRESHOLD_RATIO # a küszöb legyen a csúcs valahány százaléka

        offset_time = times[peak_frame] # elkezdjük követni a lecsengést

        for j in range(peak_frame + 1, magnitude.shape[1]):
            current_time = times[j]

            if current_time >= next_onset:
                offset_time = next_onset - self.OFFSET_MARGIN # ha nagyon összecsúszna az onset és offset, akkor a következő onset-ig követjük csak a lecsengést
                break

            current_salience = self.get_f0_salience(f0, j, magnitude, freqs, self.fs, max_harmonics)

            if current_salience < salience_treshold:
                offset_time = current_time
                break

            offset_time = current_time

        return offset_time

    def note_rec(self, max_harmonics, tuning="E"):
        # gitár hangok frekvenciái
        guitar_note_freqs = GuitarNoteFreqs()
        guitar_notes = guitar_note_freqs.select_tuning(tuning)
        guitar_notes_arr = np.asarray(guitar_notes, dtype=float)

        # ONSET DETEKTÁLÁS
        onset_detect = OnsetDetect(self.filtered, fs=self.fs)
        onsets = onset_detect.get_onsets(min_gap=0.05)
        self.onsets = onsets

        print(f"Onsetek ({len(onsets)} db): {[round(t, 2) for t in onsets]}")

        notes_with_offsets = []
        freqs = lb.fft_frequencies(sr=self.fs, n_fft=self.NFFT)

        for i in range(len(onsets)):
            onset = onsets[i]
            next_onset = onsets[i + 1] if i < len(onsets) - 1 else (onset + self.MAX_NOTE_LENGTH)

            audio_slice = self._onset_slice(onset, next_onset)
            if audio_slice is None: # ha túl rövid a szelet, kihagyom
                continue

            frames = self._slice_frames(audio_slice, onset)
            if frames is None:
                continue
            magnitude, times, start_frame, end_frame = frames

            # HANGMAGASSÁG
            f0 = self._estimate_pitch(audio_slice, start_frame, end_frame, max_harmonics, guitar_notes, guitar_notes_arr)
            if f0 is None:
                print(f"Az onset (t={onset:.2f}s) körül nincs hang")
                continue

            # rezonancia szűrés: az előző hanghoz túl közeli onset nem új hang
            if notes_with_offsets and onset - notes_with_offsets[-1].onset < self.DUPLICATE_GAP:
                continue

            # OFFSET DETEKTÁLÁS
            offset = self._find_offset(f0, onset, next_onset, magnitude, freqs, times, start_frame, end_frame, max_harmonics)
            notes_with_offsets.append(NoteEvent(onset, offset, f0)) # minden egyes hangról egy NoteEvent objektumot tárolunk el

        for note in notes_with_offsets:
            print(f"Felismert hang: {note.note_name} - {note.freq:.2f} Hz, onset: {note.onset:.2f} s, offset: {note.offset:.2f} s")
        print(f"Felismert hangok száma: {len(notes_with_offsets)}")

        return notes_with_offsets
