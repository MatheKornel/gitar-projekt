import librosa as lb
from music21 import stream, note, duration, meter, environment, clef
import os
import subprocess

lilypond_path = r"D:\lilypond-2.24.4\bin\lilypond.exe"

if os.path.exists(lilypond_path):
    env = environment.Environment()
    env['lilypondPath'] = lilypond_path
    print(f"LilyPond útvonal beállítva: {lilypond_path}")
else:
    print("Hiba: A LilyPond útvonal nincs beállítva vagy nem létezik.")

class SheetMusicExporter:
    def __init__(self, tempo=120):
        self.sec_per_beat = 60 / tempo
    
    # létrehozza a kottát a felismert hangok alapján, majd elmenti PDF formátumban és megjeleníti PNG-ként
    def create_score(self, notes, file_basename="output"):
        score = stream.Score()
        part = stream.Part()

        part.append(meter.TimeSignature('4/4'))
        part.clef = clef.TrebleClef() # violinkulcs
        last_offset = 0.0

        for note_event in notes:
            pause_duration = note_event.onset - last_offset # szünet hozzáadása, ha szükséges
            if pause_duration > 0.05:
                pause_quarter_length = pause_duration / self.sec_per_beat
                pause_quarter_length = round(pause_quarter_length * 8) / 8.0 # kvantálás 32-ed értékre
                rest = note.Rest(quarterLength=pause_quarter_length)
                part.append(rest)
            
            n = note.Note() # hang létrehozása
            n.pitch.midi = note_event.midi_note + 12 # oktávval feljebb, hogy "gitáros" kotta legyen

            note_quarter_length = note_event.duration / self.sec_per_beat # időtartam beállítása
            note_quarter_length = round(note_quarter_length * 8) / 8.0 # kvantálás 32-ed értékre
            n.duration = duration.Duration(quarterLength=note_quarter_length)
            part.append(n)

            last_offset = note_event.offset # frissítjük az utolsó offsetet

        score.append(part)

        # mentés PDF-be és PNG-be
        target_dir = "sheet_music"
        os.makedirs(target_dir, exist_ok=True)

        base_output_path = os.path.join(target_dir, file_basename)
        ly_file_path = f"{base_output_path}.ly"

        try:
            # Lilypond
            score.write('lilypond', fp=ly_file_path)

            # PDF
            subprocess.run([lilypond_path, "-f", "pdf", "-o", base_output_path, ly_file_path], check=True, capture_output=True, text=True)
            pdf_path = f"{base_output_path}.pdf"

            # PNG
            #subprocess.run([lilypond_path, "-f", "png", "-o", base_output_path, ly_file_path], check=True, capture_output=True, text=True)
            #png_path = f"{base_output_path}.png"

            print(f"Kotta mentve: {target_dir}")
            return (pdf_path)
        except Exception as e:
            print(f"Hiba a kotta generálásánál: {e}")
            return (None, None)
        finally:
            os.remove(ly_file_path)