from music21 import stream, note, duration, meter, environment, clef, tempo, instrument
import os
import re
import subprocess
from quantizing import Quantizing

lilypond_path = r"D:\lilypond-2.24.4\bin\lilypond.exe"

if os.path.exists(lilypond_path):
    env = environment.Environment()
    env['lilypondPath'] = lilypond_path
    print(f"LilyPond útvonal beállítva: {lilypond_path}")
else:
    print("Hiba: A LilyPond útvonal nincs beállítva vagy nem létezik.")

class SheetMusicTabExporter:
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

        quantizer = Quantizing(notes)
        current_beat = 0.0
        for i, note_event in enumerate(notes):
            quant_onset, quant_offset = quantizer.quantize(note_event, i, self.sec_per_beat, current_beat)
                
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

        # tabulatúra generálás és mentés PDF-be
        target_dir = "sheet_music"
        os.makedirs(target_dir, exist_ok=True)

        try:
            ly_path_full = os.path.join(target_dir, f"{file_basename}.ly")
            final_part.write('lily', fp=ly_path_full)

            with open(ly_path_full, 'r', encoding='utf-8') as f:
                ly_code = f.read()

            ly_code = re.sub(r'\\header\s*\{', f'\\\\header {{\n  title = "{file_basename}"', ly_code, count=1)
            ly_code = re.sub(r'\\clef\s+"?[a-zA-Z0-9_]+"?', '', ly_code)
            ly_code = ly_code.replace("\\new Voice {", "{")
            ly_code = re.sub(r'\\include "lilypond-book-preamble\.ly"', '', ly_code)
            ly_code = re.sub(r'\\score\s*\{', 'melody = {', ly_code, count=1)
            new_score_block = """
\\score {
  <<
    \\new Staff { \\melody }
    \\new TabStaff { \\new TabVoice { \\transpose c c, { \\melody } } }
  >>
  \\layout {
    indent = 0\\mm
  }
}
"""
            if "\\paper" in ly_code:
                ly_code = ly_code.replace("\\paper", new_score_block + "\n\\paper", 1)
            else:
                ly_code += new_score_block

            with open(ly_path_full, 'w', encoding='utf-8') as f:
                f.write(ly_code)

            pdf_path_full = os.path.join(target_dir, f"{file_basename}.pdf")
            lilypond_exe = environment.Environment()['lilypondPath']
            subprocess.run([lilypond_exe, "--pdf", "-o", os.path.join(target_dir, file_basename), ly_path_full], check=True)
            
            if os.path.exists(pdf_path_full):
                print(f"Kotta és tabulatúra sikeresen generálva: {pdf_path_full}")
                os.startfile(pdf_path_full)

            if os.path.exists(ly_path_full):
                os.remove(ly_path_full)
            return pdf_path_full
        
        except subprocess.CalledProcessError as e:
            print(f"Hiba történt a Lilypond futtatásakor: {e}")
            return None
        except Exception as e:
            print(f"Hiba a kotta és tabulatúra generálásánál: {e}")
            return None