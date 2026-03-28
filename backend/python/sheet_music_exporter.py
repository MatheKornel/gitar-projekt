from music21 import stream, note, duration, meter, environment, clef, tempo, instrument
import os

lilypond_path = r"D:\lilypond-2.24.4\bin\lilypond.exe"

if os.path.exists(lilypond_path):
    env = environment.Environment()
    env['lilypondPath'] = lilypond_path
    print(f"LilyPond útvonal beállítva: {lilypond_path}")
else:
    print("Hiba: A LilyPond útvonal nincs beállítva vagy nem létezik.")

class SheetMusicExporter:
    def __init__(self, audio_tempo=120):
        self.sec_per_beat = 60 / audio_tempo # másodperc per negyedhang
        self.audio_tempo = audio_tempo # tempó a kotta számára
    
    # létrehozza a kottát a felismert hangok alapján, majd elmenti PDF formátumban és megjeleníti
    def create_score(self, notes, file_basename="output"):
        part = stream.Stream()
        part.insert(0, instrument.Guitar()) # gitár hangszer hozzáadása

        part.append(meter.TimeSignature('4/4'))
        part.append(tempo.MetronomeMark(number=self.audio_tempo))
        part.clef = clef.TrebleClef() # violinkulcs
        current_beat = 0.0
        grid_resolution = 0.25 # 16-od értékekre kvantálás

        for i, note_event in enumerate(notes):
            beat_onset = note_event.onset / self.sec_per_beat # időpontok átszámítása negyedhangokra
            beat_offset = note_event.offset / self.sec_per_beat

            quant_onset = round(beat_onset / grid_resolution) * grid_resolution # kvantálás a legközelebbi grid pontokra
            quant_offset = round(beat_offset / grid_resolution) * grid_resolution

            if quant_offset <= quant_onset:
                quant_offset = quant_onset + grid_resolution

            if i < len(notes) - 1:
                next_note = notes[i + 1]
                next_beat_onset = next_note.onset / self.sec_per_beat
                next_quant_onset = round(next_beat_onset / grid_resolution) * grid_resolution
                gap = next_quant_onset - quant_offset
                if gap < 0.5 and next_quant_onset > quant_onset:
                    quant_offset = next_quant_onset # nagyon rövid szünetek elkerülése

            if quant_offset <= quant_onset:
                quant_offset = quant_onset + grid_resolution # ha 0-ra kvantálna, legalább egy 16-od érték legyen
                
            rest_duration = quant_onset - current_beat
            if rest_duration > 0:
                rest = note.Rest(quarterLength=rest_duration)
                part.append(rest) # szünet hozzáadása, ha van

            n = note.Note() # hang létrehozása
            n.pitch.midi = note_event.midi_note + 12 # oktávval feljebb, hogy "gitáros" kotta legyen
            note_duration = quant_offset - quant_onset
            n.duration = duration.Duration(quarterLength=note_duration)
            part.append(n)
            current_beat = quant_offset # frissítjük az aktuális beatet
        
        final_part = part.makeMeasures()

        # mentés PDF-be
        target_dir = "sheet_music"
        os.makedirs(target_dir, exist_ok=True)

        try:
            pdf_path_full = os.path.join(target_dir, f"{file_basename}")
            final_part.show('lily.pdf', fp=pdf_path_full)
            pdf_path = pdf_path_full

            print(f"Kotta mentve: {target_dir}")
            return pdf_path
        except Exception as e:
            print(f"Hiba a kotta generálásánál: {e}")
            return None
        finally:
            os.remove(pdf_path_full)