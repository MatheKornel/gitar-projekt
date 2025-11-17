import librosa as lb
import numpy as np

class NoteEvent:
    def __init__(self, onset, offset, freq, velocity=64):
        self.onset = onset      # hang kezdete (másodpercben)
        self.offset = offset    # hang vége (másodpercben)
        self.freq = freq        # hang frekvenciája (Hz)
        self.duration = offset - onset  # hang hossza (másodpercben)
        self.velocity = velocity  # hangerő (0-127)

        try:
            self.midi_note = int(np.round(69 + 12 * np.log2(freq / 440.0)))  # frekvencia átváltása MIDI hangra
            self.note_name = lb.midi_to_note(self.midi_note)  # MIDI hangnév lekérése
        except Exception:
            self.midi_note = 0
            self.note_name = "Ismeretlen"
