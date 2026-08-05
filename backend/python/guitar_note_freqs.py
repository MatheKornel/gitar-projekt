from collections import deque

class GuitarNoteFreqs:
    def __init__(self):
        self.guitar_notes = deque([
                    82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81,
                    138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65,
                    220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63,
                    349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25,
                    554.37, 587.33, 622.25, 659.25, 698.46, 739.99, 783.99, 830.61,
                    880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51], maxlen=49)

        def select_tuning(self, tuning):
            match tuning:
                case "E":
                    return self.guitar_notes
                case "D# / Eb":
                    return self.guitar_notes.appendleft(77.78)
                case "D":
                    return self.guitar_notes.appendleft(73.42)
                case "C# / Db":
                    return self.guitar_notes.appendleft(69.30)
                case "C":
                    return self.guitar_notes.appendleft(65.41)
                case "B":
                    return self.guitar_notes.appendleft(61.74)
                case "A# / Bb":
                    return self.guitar_notes.appendleft(58.27)
                case "A":
                    return self.guitar_notes.appendleft(55.00)
                case "G# / Ab":
                    return self.guitar_notes.appendleft(51.91)
                case "G":
                    return self.guitar_notes.appendleft(49.00)
                case "F# / Gb":
                    return self.guitar_notes.appendleft(46.25)
                case "F":
                    return self.guitar_notes.appendleft(43.65)
