from collections import deque

class GuitarNoteFreqs:
    TUNING_STEPS = {
                    "E": 0, "D# / Eb": 1, "D": 2, "C# / Db": 3,
                    "C": 4, "B": 5, "A# / Bb": 6, "A": 7,
                    "G# / Ab": 8, "G": 9, "F# / Gb": 10, "F": 11
                    }
    
    def __init__(self):
        self.guitar_notes = deque([
                    82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81,
                    138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65,
                    220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63,
                    349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25,
                    554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99, 830.61,
                    880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51], maxlen=49)

    def select_tuning(self, tuning):
                lower_notes = [77.78, 73.42, 69.30, 65.41, 61.74, 58.27, 55.00, 51.91, 49.00, 46.25, 43.65]

                steps = self.TUNING_STEPS.get(tuning, 0)
                d = deque(self.guitar_notes, maxlen=49)
                if steps > 0:
                    d.extendleft(lower_notes[:steps])
    
                return d
