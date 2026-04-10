class Quantizing:
    def __init__(self, notes, grid_resolution=0.25):
        self.notes = notes
        self.grid_resolution = grid_resolution

    def quantize(self, note_event, i, sec_per_beat, current_beat):
        beat_onset = note_event.onset / sec_per_beat # időpontok átszámítása negyedhangokra
        beat_offset = note_event.offset / sec_per_beat

        quant_onset = round(beat_onset / self.grid_resolution) * self.grid_resolution # kvantálás a legközelebbi grid pontokra
        quant_offset = round(beat_offset / self.grid_resolution) * self.grid_resolution

        if quant_offset <= quant_onset:
            quant_offset = quant_onset + self.self.grid_resolution

        if i < len(self.notes) - 1:
            next_note = self.notes[i + 1]
            next_beat_onset = next_note.onset / sec_per_beat
            next_quant_onset = round(next_beat_onset / self.grid_resolution) * self.grid_resolution
            gap = next_quant_onset - quant_offset
            if gap < 0.5 and next_quant_onset > quant_onset:
                quant_offset = next_quant_onset # nagyon rövid szünetek elkerülése

        if quant_offset <= quant_onset:
            quant_offset = quant_onset + self.grid_resolution # ha 0-ra kvantálna, legalább egy 16-od érték legyen
                
        return quant_onset, quant_offset