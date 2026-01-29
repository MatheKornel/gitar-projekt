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
    
    # létrehozza a kottát a felismert hangok alapján, majd elmenti PDF formátumban és megjeleníti PNG-ként
    def create_score(self, notes, file_basename="output"):
        part = stream.Stream()
        part.insert(0, instrument.Guitar()) # gitár hangszer hozzáadása

        part.append(meter.TimeSignature('4/4'))
        part.append(tempo.MetronomeMark(number=self.audio_tempo))
        part.clef = clef.TrebleClef() # violinkulcs
        last_offset = 0.0

        for note_event in notes:
            pause_duration = note_event.onset - last_offset # szünet hozzáadása, ha szükséges
            if pause_duration > 0.05:
                pause_quarter_length = pause_duration / self.sec_per_beat
                pause_quarter_length = round(pause_quarter_length * 4) / 4.0 # kvantálás 32-ed értékre
                rest = note.Rest(quarterLength=pause_quarter_length)
                part.append(rest)
            
            n = note.Note() # hang létrehozása
            n.pitch.midi = note_event.midi_note + 12 # oktávval feljebb, hogy "gitáros" kotta legyen

            note_quarter_length = note_event.duration / self.sec_per_beat # időtartam beállítása
            note_quarter_length = round(note_quarter_length * 4) / 4.0 # kvantálás 32-ed értékre
            note_quarter_length = 1/32 if note_quarter_length == 0 else note_quarter_length # legyen legalább 32-ed érték
            n.duration = duration.Duration(quarterLength=note_quarter_length)
            part.append(n)

            last_offset = note_event.offset # frissítjük az utolsó offsetet
        
        final_part = part.makeMeasures().quantize(inPlace=False)

        # mentés PDF-be
        target_dir = "sheet_music"
        os.makedirs(target_dir, exist_ok=True)

        try:
            # PDF
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