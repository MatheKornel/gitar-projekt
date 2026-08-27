import os
import re
import subprocess

from music21 import stream, note, duration, meter, environment, clef, tempo, instrument

from guitar_note_freqs import GuitarNoteFreqs
from config_parameters import ProjectConfig
from config_paths import ProjectPaths
from quantizing import Quantizing


_NOTES_RE = re.compile(
    r"(?<!\\)(?P<rest>\br(?:\s*\d+\.*)?\b)" # szünetek felismerése
    r"|(?<!\\)(?P<note>\b[a-g](?:is|es)*[',]*(?:\s*\d+\.*)?)(?![a-zA-Z])(?P<tie>\s*~?)" # hangok és kötések felismerése
)

_PITCH_CLASS_NAMES = ['c', 'cis', 'd', 'dis', 'e', 'f', 'fis', 'g', 'gis', 'a', 'ais', 'b']

# a MIDI számot átalakítja Lilypond hangnév formátumra (pl. 64 -> e')
def _lily_pitch_name(midi):
    pitch_class = midi % 12
    name = _PITCH_CLASS_NAMES[pitch_class]
    octave = midi // 12 - 1
    marks = octave - 3
    if marks > 0:
        name += "'" * marks
    elif marks < 0:
        name += "," * (-marks)
    return name

# a gitár hangolásához szükséges MIDI számokat adja vissza a hangolás címkéjéből
def _tuning_midi_from_label(tuning_label):
    return GuitarNoteFreqs.open_string_midis(tuning_label)

# custom-tuning = \stringTuning <e' a' d'' g'' b'' e''>  --> lilypond kód generálása a gitár hangolásához
def _build_string_tuning_ly(tuning_midi):
    pitch_names = [_lily_pitch_name(midi) for midi in tuning_midi]
    return "custom-tuning = \\stringTuning <" + " ".join(pitch_names) + ">\n"

# megkeresi a "melody = {" első és utolsó zárójelét, és visszaadja a kezdő és záró indexet --> itt kell módosítani, hogy a megfelelő helyre szúrjuk be a tab számokat
def _lilypond_brace_search(text, start_marker):
    start = text.index(start_marker)
    brace_open = text.index('{', start)
    depth = 0
    i = brace_open
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return brace_open, i
        i += 1
    raise ValueError(f"Nem található lezáró '}}' a(z) '{start_marker}' blokkhoz.")

# a kivágott részben a hangokhoz hozzáadja a tab számokat, ha vannak
def _insert_string_numbers(melody_body, notes):
    result = []
    pos = 0
    note_idx = 0
    skip_tie_continuation = False

    for m in _NOTES_RE.finditer(melody_body):
        result.append(melody_body[pos:m.start()])
        pos = m.end()

        if m.group('rest'):
            result.append(m.group(0))
            skip_tie_continuation = False
            continue

        tie = m.group('tie') or ''
        token_text = m.group('note') + tie

        if skip_tie_continuation:
            result.append(token_text)
            skip_tie_continuation = '~' in tie
            continue

        if note_idx < len(notes):
            note_event = notes[note_idx]
            string_num = getattr(note_event, 'opt_string_num', None)
            if string_num is not None:
                token_text = f"{m.group('note')}\\{string_num}{tie}"
            note_idx += 1

        skip_tie_continuation = '~' in tie
        result.append(token_text)

    result.append(melody_body[pos:])
    return ''.join(result)


class SheetMusicTabExporter:
    def __init__(self, audio_tempo=120, paths=None, config=None):
        self.sec_per_beat = 60 / audio_tempo
        self.audio_tempo = audio_tempo
        self.paths = paths or ProjectPaths()
        self.config = config or ProjectConfig()

        self.env = environment.Environment()
        if os.path.exists(self.config.lilypond_path):
            self.env['lilypondPath'] = self.config.lilypond_path
            print(f"LilyPond útvonal beállítva: {self.config.lilypond_path}")
        else:
            print("Hiba: A LilyPond útvonal nincs beállítva vagy nem létezik.")

    def create_score(self, notes, file_basename="output", tuning="E"):
        tuning_midi = _tuning_midi_from_label(tuning)
        part = stream.Stream()
        part.insert(0, instrument.Guitar())

        part.append(meter.TimeSignature(self.config.default_time_signature))
        part.append(tempo.MetronomeMark(number=self.audio_tempo))
        part.clef = clef.TrebleClef()

        quantizer = Quantizing(notes)
        current_beat = 0.0
        for i, note_event in enumerate(notes):
            quant_onset, quant_offset = quantizer.quantize(note_event, i, self.sec_per_beat)

            rest_duration = quant_onset - current_beat
            if rest_duration > 0:
                rest = note.Rest(quarterLength=rest_duration)
                part.append(rest)

            n = note.Note()
            n.pitch.midi = note_event.midi_note + 12
            note_duration = quant_offset - quant_onset
            n.duration = duration.Duration(quarterLength=note_duration)
            part.append(n)
            current_beat = quant_offset

        final_part = part.makeMeasures()

        target_dir = self.paths.sheet_output_dir
        os.makedirs(target_dir, exist_ok=True)

        try:
            ly_path_full = os.path.join(target_dir, f"{file_basename}.ly")
            final_part.write('lily', fp=ly_path_full)

            with open(ly_path_full, 'r', encoding='utf-8') as f:
                ly_code = f.read()

            ly_code = re.sub(
                r'\\header\s*\{',
                f'\\\\header {{\n  title = "{file_basename}"\n  subtitle = "Hangolás: {tuning}"',
                ly_code, count=1
            )
            ly_code = re.sub(r'\\clef\s+"?[a-zA-Z0-9_]+"?', '', ly_code)
            ly_code = ly_code.replace("\\new Voice {", "{")
            ly_code = re.sub(r'\\include "lilypond-book-preamble\.ly"', '', ly_code)
            ly_code = re.sub(r'\\score\s*\{', 'melody = {', ly_code, count=1)

            brace_open, brace_close = _lilypond_brace_search(ly_code, 'melody = {')
            melody_body = ly_code[brace_open + 1:brace_close]
            tab_body = _insert_string_numbers(melody_body, notes)

            tabmelody_block = "\ntabmelody = {" + tab_body + "}\n"
            ly_code = ly_code[:brace_close + 1] + tabmelody_block + ly_code[brace_close + 1:]

            tuning_ly = _build_string_tuning_ly(tuning_midi)
            ly_code = tuning_ly + "\n" + ly_code

            new_score_block = """
\\score {
  <<
    \\new Staff { \\melody }
    \\new TabStaff \\with { stringTunings = #custom-tuning } {
      \\new TabVoice { \\transpose c c, { \\tabmelody } }
    }
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
            lilypond_exe = self.env['lilypondPath']
            subprocess.run([lilypond_exe, "--pdf", "-o", os.path.join(target_dir, file_basename), ly_path_full], check=True)

            if os.path.exists(pdf_path_full):
                print(f"Kotta és tabulatúra sikeresen generálva: {pdf_path_full}")
                if hasattr(os, "startfile"):
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